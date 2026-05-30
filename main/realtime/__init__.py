"""
Realtime voice conversion module for Hyper-RVC.

Provides server-mode (sounddevice) realtime voice-to-voice conversion
without audio separation (UVR). Uses the existing RVC pipeline with
circular buffers, SOLA crossfade, and silence detection for smooth
streaming output.

Architecture (simplified from deiteris/voice-changer):

  Physical Mic -> sounddevice callback -> RVC inference -> sounddevice output -> Speakers
"""

import os
import sys
import time
import threading
import numpy as np

now_dir = os.getcwd()
sys.path.append(now_dir)

try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False

from main.tools.logger import get_logger

logger = get_logger(__name__)


class RealtimeVC:
    """
    Realtime voice conversion engine.

    Uses sounddevice for audio I/O and the existing RVC VoiceConverter
    for inference. Audio is processed in fixed-size blocks with:
      - Circular buffers for context accumulation
      - SOLA (Synchronized Overlap-Add) crossfade for seamless stitching
      - Silence gating to skip quiet input
      - Volume normalization
    """

    def __init__(
        self,
        block_frame=128,
        crossfade_size=0.1,
        extra_size=0.5,
        sola_search_size=0.01,
        silence_threshold=0.001,
        sample_rate=48000,
    ):
        """
        Args:
            block_frame: Audio block size in frames. Default 128 (one worklet frame).
            crossfade_size: Crossfade overlap in seconds.
            extra_size: Extra context to feed RVC in seconds (look-ahead).
            sola_search_size: SOLA search window in seconds.
            silence_threshold: RMS threshold below which input is silence.
            sample_rate: Audio device sample rate (Hz).
        """
        self.sample_rate = sample_rate
        self.block_frame = block_frame
        self.crossfade_frame = int(crossfade_size * sample_rate)
        self.extra_frame = int(extra_size * sample_rate)
        self.sola_search_frame = int(sola_search_size * sample_rate)
        self.silence_threshold = silence_threshold

        # RVC pipeline components (set via load_model)
        self.vc = None
        self.hubert_model = None
        self.net_g = None
        self.tgt_sr = None
        self.version = None
        self.use_f0 = None
        self.sid = 0
        self.index = None
        self.big_npy = None

        # Conversion settings (hot-swappable)
        self.f0_method = "rmvpe"
        self.index_rate = 0.75
        self.pitch = 0
        self.filter_radius = 3
        self.protect = 0.33
        self.f0_autotune = False
        self.hop_length = 64

        # Internal state
        self._running = False
        self._stream = None
        self._lock = threading.Lock()

        # Audio buffers
        self._audio_buffer = None
        self._convert_buffer = None
        self._sola_buffer = None

        # Performance tracking
        self._latency_ms = 0.0
        self._volume_db = -60.0
        self._inference_time_ms = 0.0

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def load_model(self, model_path, index_path="", sid=0, embedder_model="contentvec"):
        """Load RVC model and optional index into the realtime engine."""
        from main.rvc.engine.infer.infer import VoiceConverter

        self.vc = VoiceConverter()
        self.sid = sid

        # Load embedder (HuBERT / ContentVec)
        if not self.vc.hubert_model or embedder_model != self.vc.last_embedder_model:
            self.vc.load_hubert(embedder_model)
            self.vc.last_embedder_model = embedder_model

        self.hubert_model = self.vc.hubert_model

        # Load RVC model
        self.vc.get_vc(model_path, sid)
        self.net_g = self.vc.net_g
        self.tgt_sr = self.vc.tgt_sr
        self.version = self.vc.version
        self.use_f0 = self.vc.use_f0
        self.n_spk = self.vc.n_spk

        # Load FAISS index
        self._load_index(index_path)

        # Allocate buffers
        self._alloc_buffers()

        logger.info(
            f"Realtime model loaded: {model_path} (sr={self.tgt_sr}, v={self.version})"
        )

    def _load_index(self, index_path):
        """Load FAISS index file for feature retrieval."""
        self.index = None
        self.big_npy = None

        if not index_path or not os.path.exists(index_path):
            return

        try:
            import faiss

            file_index = (
                index_path.strip().strip('"').strip("\n").strip('"').strip()
            )
            self.index = faiss.read_index(file_index)
            self.big_npy = self.index.reconstruct_n(0, self.index.ntotal)
            logger.info(f"Index loaded: {index_path} ({self.index.ntotal} vectors)")
        except Exception as e:
            logger.warning(f"Failed to load index: {e}")

    def _alloc_buffers(self):
        """Pre-allocate circular audio buffers on CPU."""
        # Audio buffer for volume measurement (16kHz context)
        buf_len = self.block_frame + self.crossfade_frame + self.sola_search_frame + self.extra_frame
        self._audio_buffer = np.zeros(buf_len, dtype=np.float32)

        # Convert buffer for RVC input (16kHz)
        self._convert_buffer = np.zeros(buf_len, dtype=np.float32)

        # SOLA crossfade buffer
        self._sola_buffer = np.zeros(self.crossfade_frame, dtype=np.float32)

    # ------------------------------------------------------------------
    # Core processing
    # ------------------------------------------------------------------

    def _circular_write(self, new_data, buffer):
        """Shift buffer left and append new data (circular write)."""
        length = len(new_data)
        buffer[:-length] = buffer[length:].copy()
        buffer[-length:] = new_data

    def _resample(self, audio, from_sr, to_sr):
        """Resample audio between sample rates."""
        if from_sr == to_sr:
            return audio
        import librosa

        return librosa.resample(audio, orig_sr=from_sr, target_sr=to_sr)

    def process_audio_block(self, audio_in):
        """
        Process a single audio block through the RVC pipeline.

        Args:
            audio_in: float32 numpy array of shape (block_frame,)

        Returns:
            float32 numpy array of shape (block_frame,) — converted audio,
            or None if silence detected.
        """
        start_time = time.time()

        # Volume check
        rms = np.sqrt(np.mean(audio_in ** 2))
        self._volume_db = 20 * np.log10(rms + 1e-10)

        if rms < self.silence_threshold:
            return None

        # Resample to 16kHz for RVC
        audio_16k = self._resample(audio_in, self.sample_rate, 16000)

        # Circular write to convert buffer
        self._circular_write(audio_16k, self._convert_buffer)

        # Get padded buffer for RVC (with context)
        padded = self._convert_buffer.copy()

        # Run RVC pipeline
        try:
            with self._lock:
                result = self._run_rvc_inference(padded)
        except Exception as e:
            logger.error(f"RVC inference error: {e}")
            return None

        if result is None or len(result) == 0:
            return None

        # Resample back to output sample rate
        result = self._resample(result, self.tgt_sr, self.sample_rate)

        # SOLA crossfade
        output = self._sola_crossfade(result)

        # Track latency
        self._inference_time_ms = (time.time() - start_time) * 1000

        return output

    def _run_rvc_inference(self, audio):
        """
        Run the RVC voice conversion pipeline on a padded audio buffer.

        Returns only the newly generated samples (without padding).
        """
        from scipy import signal

        # High-pass filter
        bh, ah = signal.butter(5, 48, btype="high", fs=16000)
        audio = signal.filtfilt(bh, ah, audio)

        # Pad for RVC context window
        window = 160
        audio_pad = np.pad(audio, (window // 2, window // 2), mode="reflect")

        # F0 extraction
        p_len = audio_pad.shape[0] // window
        sid_t = np.array([self.sid])

        if self.use_f0:
            pitch, pitchf = self.vc.vc.get_f0(
                input_audio_path=None,
                x=audio_pad,
                p_len=p_len,
                pitch=self.pitch,
                f0_method=self.f0_method,
                filter_radius=self.filter_radius,
                hop_length=self.hop_length,
                f0_autotune=self.f0_autotune,
                inp_f0=None,
            )
            pitch = pitch[:p_len]
            pitchf = pitchf[:p_len]
        else:
            pitch = None
            pitchf = None

        # Voice conversion
        output = self.vc.vc.voice_conversion(
            model=self.hubert_model,
            net_g=self.net_g,
            sid=sid_t,
            audio0=audio_pad,
            pitch=pitch,
            pitchf=pitchf,
            index=self.index,
            big_npy=self.big_npy,
            index_rate=self.index_rate,
            version=self.version,
            protect=self.protect,
        )

        # Trim padding (t_pad_tgt on each side)
        t_pad_tgt = self.tgt_sr * self.vc.vc.x_pad
        if len(output) > 2 * t_pad_tgt:
            output = output[t_pad_tgt:-t_pad_tgt]
        elif len(output) > t_pad_tgt:
            output = output[t_pad_tgt:]

        # Volume normalization
        audio_max = np.abs(output).max() / 0.99
        if audio_max > 1:
            output /= audio_max

        return output.astype(np.float32)

    def _sola_crossfade(self, audio_out):
        """
        Apply SOLA (Synchronized Overlap-Add) crossfade between
        the new audio and previous buffer for seamless stitching.
        """
        if self._sola_buffer is None or self.crossfade_frame == 0:
            return audio_out[: self.block_frame]

        cf = self.crossfade_frame
        ss = self.sola_search_frame

        if len(audio_out) < cf + ss + self.block_frame:
            # Not enough audio for crossfade, just return what we can
            result = audio_out[: self.block_frame]
            self._sola_buffer = audio_out[-cf:].copy() if len(audio_out) >= cf else np.zeros(cf, dtype=np.float32)
            return result

        # Find optimal SOLA offset via cross-correlation
        prev_tail = self._sola_buffer
        search_start = cf
        search_end = min(cf + ss + 1, len(audio_out) - self.block_frame + cf)

        best_offset = cf
        best_corr = -float("inf")

        for offset in range(search_start, search_end):
            segment = audio_out[offset - cf : offset]
            corr = np.dot(prev_tail, segment) / (
                np.linalg.norm(prev_tail) * np.linalg.norm(segment) + 1e-10
            )
            if corr > best_corr:
                best_corr = corr
                best_offset = offset

        # Apply sinusoidal crossfade
        fade_in = np.sin(np.linspace(0, np.pi / 2, cf)) ** 2
        fade_out = np.cos(np.linspace(0, np.pi / 2, cf)) ** 2

        audio_out[best_offset - cf : best_offset] = (
            prev_tail * fade_out + audio_out[best_offset - cf : best_offset] * fade_in
        )

        # Return exactly block_frame samples
        result = audio_out[best_offset : best_offset + self.block_frame]

        # Update SOLA buffer
        self._sola_buffer = audio_out[
            best_offset + self.block_frame - cf : best_offset + self.block_frame
        ].copy()

        return result

    # ------------------------------------------------------------------
    # Audio stream control
    # ------------------------------------------------------------------

    def _audio_callback(self, indata, outdata, frames, time_info, status):
        """sounddevice stream callback — processes audio inline."""
        if status:
            logger.warning(f"Audio stream status: {status}")

        # Convert to mono float32
        audio_in = indata[:, 0].astype(np.float32)
        if len(audio_in) != self.block_frame:
            # Pad or trim to match block_frame
            if len(audio_in) < self.block_frame:
                audio_in = np.pad(audio_in, (0, self.block_frame - len(audio_in)))
            else:
                audio_in = audio_in[: self.block_frame]

        # Process
        result = self.process_audio_block(audio_in)

        # Write output (pass-through silence if no conversion)
        if result is not None and len(result) == self.block_frame:
            outdata[:, 0] = result
        else:
            outdata[:, 0] = audio_in  # pass-through

    def start(
        self,
        input_device=None,
        output_device=None,
        block_size=None,
        latency="low",
    ):
        """
        Start the realtime audio stream.

        Args:
            input_device: sounddevice input device ID or name. None = default.
            output_device: sounddevice output device ID or name. None = default.
            block_size: Number of frames per block. None = auto.
            latency: 'low' or 'normal'.
        """
        if not HAS_SOUNDDEVICE:
            raise RuntimeError(
                "sounddevice is not installed. Install it with: pip install sounddevice"
            )

        if self.vc is None:
            raise RuntimeError("No model loaded. Call load_model() first.")

        bs = block_size or (self.block_frame * 128)  # ~512ms at 48kHz

        try:
            self._stream = sd.Stream(
                callback=self._audio_callback,
                latency=latency,
                dtype="float32",
                device=(input_device, output_device),
                blocksize=bs,
                samplerate=self.sample_rate,
                channels=1,
            )
            self._stream.start()
            self._running = True
            logger.info(
                f"Realtime stream started (sr={self.sample_rate}, block={bs}, latency={latency})"
            )
        except Exception as e:
            self._running = False
            raise RuntimeError(f"Failed to start audio stream: {e}")

    def stop(self):
        """Stop the realtime audio stream."""
        self._running = False
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as e:
                logger.warning(f"Error stopping stream: {e}")
            self._stream = None
        logger.info("Realtime stream stopped")

    def is_running(self):
        """Check if the realtime stream is active."""
        return self._running

    def get_status(self):
        """Get current performance stats."""
        return {
            "latency_ms": round(self._inference_time_ms, 2),
            "volume_db": round(self._volume_db, 1),
            "running": self._running,
        }

    def update_params(
        self,
        pitch=None,
        index_rate=None,
        f0_method=None,
        filter_radius=None,
        protect=None,
        f0_autotune=None,
        hop_length=None,
        silence_threshold=None,
    ):
        """Hot-swap conversion parameters while running."""
        if pitch is not None:
            self.pitch = pitch
        if index_rate is not None:
            self.index_rate = index_rate
        if f0_method is not None:
            self.f0_method = f0_method
        if filter_radius is not None:
            self.filter_radius = filter_radius
        if protect is not None:
            self.protect = protect
        if f0_autotune is not None:
            self.f0_autotune = f0_autotune
        if hop_length is not None:
            self.hop_length = hop_length
        if silence_threshold is not None:
            self.silence_threshold = silence_threshold

    def cleanup(self):
        """Release all resources."""
        self.stop()
        if self.vc is not None:
            try:
                self.vc.cleanup_model()
            except Exception:
                pass
        self.vc = None
        self.hubert_model = None
        self.net_g = None
        self._audio_buffer = None
        self._convert_buffer = None
        self._sola_buffer = None

        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("Realtime engine cleaned up")


# ------------------------------------------------------------------
# Audio device enumeration
# ------------------------------------------------------------------


def get_audio_devices():
    """
    Return dict with 'input' and 'output' lists of (name, id) tuples
    for available audio devices.
    """
    if not HAS_SOUNDDEVICE:
        return {"input": [], "output": []}

    devices = sd.query_devices()
    inputs = []
    outputs = []

    for i, dev in enumerate(devices):
        name = dev["name"]
        if dev["max_input_channels"] > 0:
            inputs.append((name, i))
        if dev["max_output_channels"] > 0:
            outputs.append((name, i))

    return {"input": inputs, "output": outputs}


# Global singleton
_engine = None


def get_engine() -> RealtimeVC:
    """Get or create the global RealtimeVC engine singleton."""
    global _engine
    if _engine is None:
        _engine = RealtimeVC()
    return _engine
