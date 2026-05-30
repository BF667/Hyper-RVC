"""
RVC voice conversion module for Hyper-RVC.

Provides a cached :class:`VoiceConverter` singleton and a thin wrapper
around ``VoiceConverter.convert_audio`` so callers don't need to import
the Applio internals directly.

Typical usage::

    from main.rvc.converter import import_voice_converter, run_rvc_conversion

    vc = import_voice_converter()
    run_rvc_conversion(
        audio_input_path="input.wav",
        audio_output_path="output.wav",
        model_path="path/to/model.pth",
        index_path="path/to/index.index",
        ...
    )
"""

import os
import sys
from functools import lru_cache
from typing import Optional

now_dir = os.getcwd()
sys.path.append(now_dir)

from main.tools.logger import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=None)
def import_voice_converter():
    """
    Import and cache the VoiceConverter instance.

    Returns:
        VoiceConverter instance for RVC inference
    """
    from main.rvc.engine.infer.infer import VoiceConverter
    return VoiceConverter()


@lru_cache(maxsize=1)
def get_config():
    """
    Get and cache the RVC configuration.

    Returns:
        RVC Config instance
    """
    from main.rvc.engine.configs.config import Config
    return Config()


def run_rvc_conversion(
    audio_input_path: str,
    audio_output_path: str,
    model_path: str,
    index_path: str,
    embedder_model: str,
    pitch: int,
    f0_method: str,
    filter_radius: int,
    index_rate: float,
    volume_envelope: float,
    protect: float,
    split_audio: bool,
    f0_autotune: bool,
    hop_length: int,
    export_format: str,
) -> None:
    """
    Run RVC voice conversion on a single audio file.

    This is a thin wrapper around
    ``VoiceConverter.convert_audio`` that accepts keyword arguments
    matching the original core.py signature.

    Args:
        audio_input_path:  Path to the input audio file.
        audio_output_path: Path to save the converted audio.
        model_path:        Path to the RVC model file (``.pth``).
        index_path:        Path to the RVC index file (``.index``).
        embedder_model:    Embedder model name (e.g. ``"contentvec"``).
        pitch:             Pitch shift in semitones.
        f0_method:         Pitch extraction method
                           (e.g. ``"rmvpe"``, ``"crepe"``).
        filter_radius:     Median filter radius around the predicted pitch.
        index_rate:        Feature search ratio (0–1).
        volume_envelope:   Mix rate of the volume envelope (0–1).
        protect:           Protection of breathy sounds (0–0.5).
        split_audio:       Whether to split the audio for better pitch
                           detection.
        f0_autotune:       Whether to snap to the nearest musical note.
        hop_length:        Hop length for pitch extraction.
        export_format:     Output format (e.g. ``"WAV"``, ``"FLAC"``).
    """
    inference_vc = import_voice_converter()
    logger.info("Making RVC inference")

    inference_vc.convert_audio(
        audio_input_path=audio_input_path,
        audio_output_path=audio_output_path,
        model_path=model_path,
        index_path=index_path,
        embedder_model=embedder_model,
        pitch=pitch,
        f0_file=None,
        f0_method=f0_method,
        filter_radius=filter_radius,
        index_rate=index_rate,
        volume_envelope=volume_envelope,
        protect=protect,
        split_audio=split_audio,
        f0_autotune=f0_autotune,
        hop_length=hop_length,
        export_format=export_format,
        embedder_model_custom=None,
    )
