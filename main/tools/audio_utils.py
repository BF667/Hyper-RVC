"""
Audio effects and merging utilities for Hyper-RVC.

Provides:
- Reverb effects via Pedalboard
- Audio merging (vocals + instrumentals + backing) via pydub
- FP16 model config patching for models that don't support half precision
"""

import os
import sys
import yaml
from typing import Dict, Any

import yaml

now_dir = os.getcwd()
sys.path.append(now_dir)

from pedalboard import Pedalboard, Reverb
from pedalboard.io import AudioFile
from pydub import AudioSegment

from main.tools.logger import get_logger

logger = get_logger(__name__)


def add_audio_effects(
    audio_path: str,
    reverb_size: float,
    reverb_wet: float,
    reverb_dry: float,
    reverb_damping: float,
    reverb_width: float,
    output_path: str,
) -> str:
    """
    Add reverb effects to an audio file using Pedalboard.

    Args:
        audio_path: Path to input audio file
        reverb_size: Room size (0-1)
        reverb_wet: Wet level (0-1)
        reverb_dry: Dry level (0-1)
        reverb_damping: Damping (0-1)
        reverb_width: Stereo width (0-1)
        output_path: Path to save the output file

    Returns:
        Path to the output file
    """
    try:
        board = Pedalboard([])
        board.append(
            Reverb(
                room_size=reverb_size,
                dry_level=reverb_dry,
                wet_level=reverb_wet,
                damping=reverb_damping,
                width=reverb_width,
            )
        )
        with AudioFile(audio_path) as f:
            with AudioFile(output_path, "w", f.samplerate, f.num_channels) as o:
                while f.tell() < f.frames:
                    chunk = f.read(int(f.samplerate))
                    effected = board(chunk, f.samplerate, reset=False)
                    o.write(effected)
        logger.info(f"Audio effects applied successfully: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error applying audio effects: {e}")
        raise


def merge_audios(
    vocals_path: str,
    inst_path: str,
    backing_path: str,
    output_path: str,
    main_gain: float,
    inst_gain: float,
    backing_Vol: float,
    output_format: str,
) -> str:
    """
    Merge multiple audio files (vocals, instrumentals, backing vocals).

    Args:
        vocals_path: Path to vocals audio file
        inst_path: Path to instrumental audio file
        backing_path: Path to backing vocals audio file
        output_path: Path to save the merged output
        main_gain: Volume gain for main vocals (dB)
        inst_gain: Volume gain for instrumentals (dB)
        backing_Vol: Volume gain for backing vocals (dB)
        output_format: Output format (e.g., 'mp3', 'flac', 'wav')

    Returns:
        Path to the merged output file
    """
    try:
        main_vocal_audio = AudioSegment.from_file(vocals_path, format="flac") + main_gain
        instrumental_audio = AudioSegment.from_file(inst_path, format="flac") + inst_gain
        backing_vocal_audio = (
            AudioSegment.from_file(backing_path, format="flac") + backing_Vol
        )
        combined_audio = main_vocal_audio.overlay(
            instrumental_audio.overlay(backing_vocal_audio)
        )
        combined_audio.export(output_path, format=output_format)
        logger.info(f"Audio files merged successfully: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error merging audio files: {e}")
        raise


def update_model_config_for_fp16(model_info: Dict[str, Any], use_fp16: bool) -> None:
    """
    Update model config file based on FP16 support.

    When *use_fp16* is ``False`` the ``training.use_amp`` flag inside the
    model's ``config.yaml`` is set to ``False`` so that the separation
    pipeline does not attempt half-precision inference on unsupported
    hardware.

    Args:
        model_info: Dictionary containing model information (must include
                    a ``"config"`` key with the path to the YAML file and a
                    ``"name"`` key for logging).
        use_fp16: Whether FP16 is supported on the target device.
    """
    if not use_fp16 and os.path.exists(model_info["config"]):
        try:
            with open(model_info["config"], "r") as file:
                config = yaml.safe_load(file)

            if "training" in config and "use_amp" in config["training"]:
                config["training"]["use_amp"] = False

            with open(model_info["config"], "w") as file:
                yaml.safe_dump(config, file)
            logger.info(f"Disabled FP16/AMP in config for {model_info['name']}")
        except Exception as e:
            logger.error(f"Error updating config for {model_info['name']}: {e}")
