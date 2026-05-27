"""
ONNXCREPE F0 predictor for Hyper-RVC.

Full CREPE pitch extraction using ONNX Runtime with Viterbi-based pitch
estimation.  This is a faithful reimplementation of the CREPE algorithm
using onnxruntime for faster inference than the PyTorch version.

Extracted from ``main.rvc.engine.lib.predictors.ONNXF0`` into its own
dedicated library module.
"""

import os
import numpy as np
import librosa

try:
    import onnxruntime as ort
except ImportError:
    ort = None

from main.tools.variables import (
    CREPE_CENTS_PER_BIN,
    CREPE_MAX_FMAX,
    CREPE_PITCH_BINS,
    CREPE_SAMPLE_RATE,
    CREPE_WINDOW_SIZE,
)

# Local aliases for backward compatibility (deprecated — use variables.py directly)
CENTS_PER_BIN = CREPE_CENTS_PER_BIN
MAX_FMAX = CREPE_MAX_FMAX
PITCH_BINS = CREPE_PITCH_BINS
SAMPLE_RATE = CREPE_SAMPLE_RATE
WINDOW_SIZE = CREPE_WINDOW_SIZE


class ONNXCrepe:
    """Full CREPE pitch extraction using ONNX Runtime.

    Loads a CREPE ONNX model and performs Viterbi-based pitch estimation.
    This is a faithful reimplementation of the CREPE algorithm using onnxruntime
    for faster inference than the PyTorch version.

    Args:
        model_path: Path to the CREPE ONNX model file (``crepe.onnx`` or ``crepe_tiny.onnx``).
        f0_min: Minimum F0 to detect in Hz.
        f0_max: Maximum F0 to detect in Hz.
        device: Execution provider device string (e.g. ``"CUDA"``, ``"CPU"``).
        sample_rate: Audio sample rate (audio will be resampled to 16 kHz internally).
        hop_length: Hop length in samples at *sample_rate* (will be converted for 16 kHz).
    """

    def __init__(
        self,
        model_path: str,
        f0_min: float = 50.0,
        f0_max: float = 1100.0,
        device: str = "CPU",
        sample_rate: int = 16000,
        hop_length: int = 160,
    ):
        if ort is None:
            raise ImportError(
                "onnxruntime is required for ONNX F0 predictors. "
                "Install it with: pip install onnxruntime or onnxruntime-gpu"
            )

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"ONNX CREPE model not found: {model_path}")

        # Set execution providers
        if device != "cpu" and "CUDA" in device.upper():
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        elif device != "cpu" and "CoreML" in device:
            providers = ["CoreMLExecutionProvider", "CPUExecutionProvider"]
        else:
            providers = ["CPUExecutionProvider"]

        self.session = ort.InferenceSession(model_path, providers=providers)
        self.f0_min = f0_min
        self.f0_max = f0_max
        self.sample_rate = sample_rate
        self.hop_length = hop_length

        # Viterbi transition matrix (pre-computed)
        self._build_transition_matrix()

    def _build_transition_matrix(self):
        """Pre-compute Viterbi transition probabilities."""
        xx, yy = np.meshgrid(range(CREPE_PITCH_BINS), range(CREPE_PITCH_BINS))
        transition = np.maximum(12 - abs(xx - yy), 0)
        self.transition = transition / transition.sum(axis=1, keepdims=True)

    def _bins_to_frequency(self, bins: np.ndarray) -> np.ndarray:
        """Convert pitch bins to frequency in Hz."""
        cents = CREPE_CENTS_PER_BIN * bins + 1997.3794084376191
        return 10.0 * 2.0 ** (cents / 1200.0)

    def _frequency_to_bins(self, frequency: float, quantize_fn=np.floor) -> int:
        """Convert frequency in Hz to pitch bin index."""
        return int(quantize_fn(((1200 * np.log2(frequency / 10)) - 1997.3794084376191) / CREPE_CENTS_PER_BIN))

    def _preprocess(self, audio: np.ndarray, pad: bool = True):
        """Preprocess audio into CREPE-format frames.

        Yields batches of frames as numpy arrays ready for ONNX inference.

        Args:
            audio: 1-D numpy array of audio samples.
            pad: Whether to zero-pad the audio.
        """
        # Resample to 16 kHz if needed
        if self.sample_rate != CREPE_SAMPLE_RATE:
            audio = librosa.resample(
                audio, orig_sr=self.sample_rate, target_sr=CREPE_SAMPLE_RATE, res_type="soxr_vhq"
            )

        hop_length_16k = int(self.hop_length * CREPE_SAMPLE_RATE / self.sample_rate)

        if pad:
            total_frames = 1 + int(audio.size // hop_length_16k)
            audio = np.pad(audio, (CREPE_WINDOW_SIZE // 2, CREPE_WINDOW_SIZE // 2))
        else:
            total_frames = 1 + int((audio.size - CREPE_WINDOW_SIZE) // hop_length_16k)

        for i in range(total_frames):
            start = i * hop_length_16k
            frame = audio[start: start + CREPE_WINDOW_SIZE]
            if len(frame) < CREPE_WINDOW_SIZE:
                frame = np.pad(frame, (0, CREPE_WINDOW_SIZE - len(frame)))
            frame = (frame - frame.mean()) / max(frame.std(), 1e-10)
            yield frame.astype(np.float32).reshape(1, -1)

    def _viterbi(self, logits: np.ndarray):
        """Apply Viterbi decoding to smooth pitch predictions."""
        bins = np.array([
            librosa.sequence.viterbi(sequence, self.transition).astype("int64")
            for sequence in logits
        ])
        return bins, self._bins_to_frequency(bins)

    def _postprocess(self, probabilities: np.ndarray):
        """Filter probabilities by f0 range and apply Viterbi decoding."""
        min_bin = self._frequency_to_bins(self.f0_min)
        max_bin = self._frequency_to_bins(self.f0_max, np.ceil)
        probabilities[:, :min_bin] = -np.inf
        probabilities[:, max_bin:] = -np.inf
        bins, pitch = self._viterbi(probabilities)
        return pitch

    def compute_f0(self, audio: np.ndarray, pad: bool = True) -> np.ndarray:
        """Compute F0 from audio.

        Args:
            audio: 1-D numpy array of audio samples (at *self.sample_rate*).
            pad: Whether to zero-pad the audio.

        Returns:
            1-D numpy array of F0 values in Hz.
        """
        results = []
        input_name = self.session.get_inputs()[0].name

        for frame in self._preprocess(audio, pad=pad):
            logits = self.session.run(None, {input_name: frame})[0]
            probs = 1.0 / (1.0 + np.exp(-logits))  # sigmoid
            results.append(probs[0])  # (PITCH_BINS,)

        if not results:
            return np.array([])

        probabilities = np.stack(results, axis=0)  # (n_frames, PITCH_BINS)
        pitch = self._postprocess(probabilities)  # (n_frames,)
        return pitch

    def infer_from_audio(self, audio: np.ndarray, thred: float = 0.03) -> np.ndarray:
        """Infer F0 from audio (compatible with RMVPE0Predictor API).

        Args:
            audio: 1-D numpy array at 16 kHz.
            thred: Unused (kept for API compatibility).

        Returns:
            1-D numpy array of F0 values in Hz.
        """
        return self.compute_f0(audio, pad=True)

    def infer_from_audio_with_pitch(self, audio, thred=0.03, f0_min=50, f0_max=1100):
        """Infer F0 from audio with explicit pitch range filtering.

        Temporarily overrides the instance ``f0_min`` / ``f0_max`` with the
        supplied values, runs the full CREPE pipeline, and restores the
        original settings before returning.

        Args:
            audio: 1-D numpy array of audio samples at *self.sample_rate*.
            thred: Unused (kept for API compatibility).
            f0_min: Minimum F0 to detect in Hz.
            f0_max: Maximum F0 to detect in Hz.

        Returns:
            1-D numpy array of F0 values in Hz.
        """
        # Save original pitch range
        orig_min, orig_max = self.f0_min, self.f0_max
        # Apply requested pitch range
        self.f0_min = f0_min
        self.f0_max = f0_max
        try:
            pitch = self.compute_f0(audio, pad=True)
        finally:
            # Restore original pitch range regardless of errors
            self.f0_min = orig_min
            self.f0_max = orig_max
        return pitch
