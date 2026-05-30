"""
Audio separation module for Hyper-RVC.

Encapsulates the five separation / cleanup stages that operate on audio
before (or after) RVC voice conversion:

1. **Vocal separation** – split a full mix into vocals + instrumentals
2. **Karaoke separation** – further split vocals into lead + backing vocals
3. **Dereverb** – remove room reverb from the lead vocal
4. **Deecho** – remove echo / flutter artifacts
5. **Denoise** – remove background noise

Each function handles both *Mel-Roformer / MDX23C* style models (invoked
via a subprocess call to ``main/uvr/models/inference.py``)
and *VR / UVR* architecture models (invoked via the ``audio_separator``
library).
"""

import os
import sys
import subprocess
import logging
from typing import Optional, Dict, Any

now_dir = os.getcwd()
sys.path.append(now_dir)

from audio_separator.separator import Separator

from main.tools.file_utils import (
    search_with_word,
    search_with_two_words,
    download_file,
    get_model_info_by_name,
)
from main.tools.audio_utils import update_model_config_for_fp16

from main.tools.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_inference_command(
    model_info: Dict[str, Any],
    input_file: str,
    store_dir: str,
    devices: str,
    use_fp16: bool,
    extract_instrumental: bool = False,
) -> list:
    """
    Build the CLI command list for ``main/uvr/models/inference.py``.

    Args:
        model_info: Model metadata dict (type, config, model, …).
        input_file: Path to the input audio.
        store_dir:  Directory to write separated stems into.
        devices:    Device string (``"cpu"`` or GPU ids separated by spaces).
        use_fp16:   Whether to enable FP16 inference.
        extract_instrumental: Whether to also extract the instrumental stem.

    Returns:
        A list of strings suitable for ``subprocess.run``.
    """
    command = [
        "python",
        os.path.join(now_dir, "main", "uvr", "models", "inference.py"),
        "--model_type",
        model_info["type"],
        "--config_path",
        model_info["config"],
        "--start_check_point",
        model_info["model"],
        "--input_file",
        input_file,
        "--store_dir",
        store_dir,
        "--flac_file",
        "--pcm_type",
        "PCM_16",
    ]

    if extract_instrumental:
        command.append("--extract_instrumental")

    if devices == "cpu":
        command.append("--force_cpu")
    else:
        device_ids = [str(int(device)) for device in devices.split()]
        command.extend(["--device_ids"] + device_ids)

    if use_fp16:
        command.append("--fp16")

    return command


def _ensure_model_files(model_info: Dict[str, Any], use_fp16: bool) -> None:
    """
    Ensure model checkpoint and config are downloaded, and patch config
    for FP16 if needed.

    Args:
        model_info: Model metadata dict.
        use_fp16:   Whether FP16 is supported.
    """
    model_ckpt_path = os.path.join(model_info["path"], "model.ckpt")
    if not os.path.exists(model_ckpt_path):
        download_file(
            model_info["model_url"],
            model_info["path"],
            "model.ckpt",
        )

    config_json_path = os.path.join(model_info["path"], "config.yaml")
    if not os.path.exists(config_json_path):
        download_file(
            model_info["config_url"],
            model_info["path"],
            "config.yaml",
        )

    update_model_config_for_fp16(model_info, use_fp16)


def _make_vr_params(use_fp16: bool, batch_size: int, use_tta: bool) -> Dict[str, Any]:
    """Build the *vr_params* dict accepted by ``Separator``."""
    vr_params: Dict[str, Any] = {
        "batch_size": batch_size,
        "enable_tta": use_tta,
    }
    if use_fp16:
        vr_params["fp16"] = True
    return vr_params


# ---------------------------------------------------------------------------
# Public separation functions
# ---------------------------------------------------------------------------

def separate_vocals(
    input_audio_path: str,
    vocal_model: str,
    store_dir: str,
    inst_dir: str,
    devices: str,
    use_fp16: bool,
) -> str:
    """
    Separate vocals from an input audio file.

    Downloads the model if necessary, runs the Mel-Roformer-based
    separation via subprocess, then moves the instrumental stem into
    *inst_dir*.

    Args:
        input_audio_path: Path to the full-mix audio file.
        vocal_model:      Name of the vocal separation model.
        store_dir:        Directory for vocal outputs.
        inst_dir:         Directory for instrumental outputs.
        devices:          GPU device string or ``"cpu"``.
        use_fp16:         Whether to use FP16 inference.

    Returns:
        Path to the instrumental file.
    """
    model_info = get_model_info_by_name(vocal_model)
    _ensure_model_files(model_info, use_fp16)

    os.makedirs(store_dir, exist_ok=True)
    os.makedirs(inst_dir, exist_ok=True)

    input_audio_basename = os.path.splitext(os.path.basename(input_audio_path))[0]

    search_result = search_with_word(store_dir, "vocals")
    if search_result:
        logger.info("Vocals already separated")
    else:
        logger.info("Separating vocals")
        command = _build_inference_command(
            model_info,
            input_audio_path,
            store_dir,
            devices,
            use_fp16,
            extract_instrumental=True,
        )
        subprocess.run(command)

        # Move the instrumental file to inst_dir
        instrumental_file = search_with_two_words(
            store_dir,
            input_audio_basename,
            "instrumental",
        )
        if instrumental_file:
            os.rename(
                os.path.join(store_dir, instrumental_file),
                os.path.join(inst_dir, f"{input_audio_basename}_instrumentals.flac"),
            )

    inst_name = search_with_two_words(inst_dir, input_audio_basename, "instrumentals")
    if inst_name is None:
        logger.warning(
            "Instrumental file not found after vocal separation for "
            f"{input_audio_basename}. The instrumental stem may not have been "
            "extracted."
        )
        return None
    inst_file = os.path.join(inst_dir, inst_name)
    return inst_file


def separate_karaoke(
    input_file: str,
    karaoke_model: str,
    store_dir: str,
    devices: str,
    use_fp16: bool,
    batch_size: int,
    use_tta: bool,
    input_audio_basename: str,
) -> None:
    """
    Separate lead vocals from backing vocals (karaoke separation).

    Supports two model families:

    * **Mel-Roformer Karaoke** – invoked via subprocess.
    * **UVR / VR architecture** – invoked via ``audio_separator.Separator``.

    Args:
        input_file:           Path to the vocal stem from the previous step.
        karaoke_model:        Name of the karaoke separation model.
        store_dir:            Directory for karaoke outputs.
        devices:              GPU device string or ``"cpu"``.
        use_fp16:             Whether to use FP16 inference.
        batch_size:           Batch size for VR models.
        use_tta:              Whether to use test-time augmentation (VR).
        input_audio_basename: Basename (without extension) of the original input.
    """
    model_info = get_model_info_by_name(karaoke_model)
    os.makedirs(store_dir, exist_ok=True)

    karaoke_exists = search_with_word(store_dir, "karaoke") is not None
    if karaoke_exists:
        logger.info("Backing vocals already separated")
        return

    logger.info("Separating backing vocals")

    if model_info["name"] == "Mel-Roformer Karaoke by aufr33 and viperx":
        _ensure_model_files(model_info, use_fp16)
        command = _build_inference_command(
            model_info,
            input_file,
            store_dir,
            devices,
            use_fp16,
            extract_instrumental=True,
        )
        subprocess.run(command)
    else:
        vr_params = _make_vr_params(use_fp16, batch_size, use_tta)
        separator = Separator(
            model_file_dir=os.path.join(now_dir, "models", "karaoke"),
            log_level=logging.WARNING,
            normalization_threshold=1.0,
            output_format="flac",
            output_dir=store_dir,
            vr_params=vr_params,
        )
        separator.load_model(model_filename=model_info["full_name"])
        separator.separate(input_file)

        # Rename UVR output files to cleaner names
        karaoke_path = store_dir
        vocals_result = search_with_two_words(
            karaoke_path, input_audio_basename, "Vocals"
        )
        instrumental_result = search_with_two_words(
            karaoke_path, input_audio_basename, "Instrumental"
        )
        if vocals_result and "UVR-BVE-4B_SN-44100-1" in os.path.basename(vocals_result):
            os.rename(
                os.path.join(karaoke_path, vocals_result),
                os.path.join(
                    karaoke_path,
                    f"{input_audio_basename}_karaoke.flac",
                ),
            )
        if instrumental_result and "UVR-BVE-4B_SN-44100-1" in os.path.basename(instrumental_result):
            os.rename(
                os.path.join(karaoke_path, instrumental_result),
                os.path.join(
                    karaoke_path,
                    f"{input_audio_basename}_instrumental.flac",
                ),
            )


def remove_reverb(
    input_file: str,
    dereverb_model: str,
    store_dir: str,
    devices: str,
    use_fp16: bool,
    batch_size: int,
    use_tta: bool,
    input_audio_basename: str,
) -> None:
    """
    Remove reverb from a vocal stem.

    Supports:
    * **BS-Roformer Dereverb / MDX23C DeReverb** – via subprocess.
    * **VR / MDX architecture** – via ``audio_separator.Separator``.

    Args:
        input_file:           Path to the karaoke vocal stem.
        dereverb_model:       Name of the dereverb model.
        store_dir:            Directory for dereverb outputs.
        devices:              GPU device string or ``"cpu"``.
        use_fp16:             Whether to use FP16 inference.
        batch_size:           Batch size for VR models.
        use_tta:              Whether to use test-time augmentation (VR).
        input_audio_basename: Basename of the original input audio.
    """
    model_info = get_model_info_by_name(dereverb_model)
    os.makedirs(store_dir, exist_ok=True)

    noreverb_exists = search_with_word(store_dir, "noreverb") is not None
    if noreverb_exists:
        logger.info("Reverb already removed")
        return

    logger.info("Removing reverb")

    if (
        model_info["name"] == "BS-Roformer Dereverb by anvuew"
        or model_info["name"] == "MDX23C DeReverb by aufr33 and jarredou"
    ):
        _ensure_model_files(model_info, use_fp16)
        command = _build_inference_command(
            model_info,
            input_file,
            store_dir,
            devices,
            use_fp16,
        )
        subprocess.run(command)
    else:
        vr_params = _make_vr_params(use_fp16, batch_size, use_tta)
        if model_info.get("arch") == "vr":
            separator = Separator(
                model_file_dir=os.path.join(now_dir, "models", "dereverb"),
                log_level=logging.WARNING,
                normalization_threshold=1.0,
                output_format="flac",
                output_dir=store_dir,
                output_single_stem="No Reverb",
                vr_params=vr_params,
            )
        else:
            separator = Separator(
                model_file_dir=os.path.join(now_dir, "models", "dereverb"),
                log_level=logging.WARNING,
                normalization_threshold=1.0,
                output_format="flac",
                output_dir=store_dir,
                output_single_stem="No Reverb",
            )
        separator.load_model(model_filename=model_info["full_name"])
        separator.separate(input_file)

        # Rename output if it came from a known UVR model
        dereverb_path = store_dir
        search_result = search_with_two_words(
            dereverb_path, input_audio_basename, "No Reverb"
        )
        if search_result and (
            "UVR-DeEcho-DeReverb" in os.path.basename(search_result)
            or "MDX Reverb HQ by FoxJoy" in os.path.basename(search_result)
        ):
            os.rename(
                os.path.join(dereverb_path, search_result),
                os.path.join(
                    dereverb_path,
                    f"{input_audio_basename}_noreverb.flac",
                ),
            )


def remove_echo(
    input_file: str,
    deecho_model: str,
    store_dir: str,
    devices: str,
    use_fp16: bool,
    batch_size: int,
    use_tta: bool,
    input_audio_basename: str,
) -> None:
    """
    Remove echo / flutter from a dereverbed vocal stem.

    Always uses the ``audio_separator.Separator`` with the *De-Echo* model.

    Args:
        input_file:           Path to the dereverbed vocal stem.
        deecho_model:         Name of the deecho model.
        store_dir:            Directory for deecho outputs.
        devices:              GPU device string or ``"cpu"``.
        use_fp16:             Whether to use FP16 inference.
        batch_size:           Batch size for VR models.
        use_tta:              Whether to use test-time augmentation.
        input_audio_basename: Basename of the original input audio.
    """
    os.makedirs(store_dir, exist_ok=True)

    no_echo_exists = search_with_word(store_dir, "noecho") is not None
    if no_echo_exists:
        logger.info("Echo already removed")
        return

    logger.info("Removing echo")
    model_info = get_model_info_by_name(deecho_model)

    vr_params = _make_vr_params(use_fp16, batch_size, use_tta)
    separator = Separator(
        model_file_dir=os.path.join(now_dir, "models", "deecho"),
        log_level=logging.WARNING,
        normalization_threshold=1.0,
        output_format="flac",
        output_dir=store_dir,
        output_single_stem="No Echo",
        vr_params=vr_params,
    )
    separator.load_model(model_filename=model_info["full_name"])
    separator.separate(input_file)

    # Rename output
    deecho_path = store_dir
    search_result = search_with_two_words(
        deecho_path, input_audio_basename, "No Echo"
    )
    if search_result and (
        "UVR-De-Echo-Normal" in os.path.basename(search_result)
        or "UVR-Deecho-Agggressive" in os.path.basename(search_result)
    ):
        os.rename(
            os.path.join(deecho_path, search_result),
            os.path.join(
                deecho_path,
                f"{input_audio_basename}_noecho.flac",
            ),
        )


def remove_noise(
    input_file: str,
    denoise_model: str,
    store_dir: str,
    deecho: bool,
    devices: str,
    use_fp16: bool,
    batch_size: int,
    use_tta: bool,
    music_folder: str,
    input_audio_basename: str,
) -> None:
    """
    Remove noise from a vocal stem.

    Supports:
    * **Mel-Roformer Denoise** – via subprocess.
    * **UVR Denoise** – via ``audio_separator.Separator``.

    The *input_file* for denoising is resolved from either the deecho
    output (if echo removal was performed) or the dereverb output.

    Args:
        input_file:           Explicit path, or the caller may pass ``None``
                              and let this function resolve it from
                              *music_folder*.
        denoise_model:        Name of the denoise model.
        store_dir:            Directory for denoise outputs.
        deecho:               Whether deecho processing was performed.
        devices:              GPU device string or ``"cpu"``.
        use_fp16:             Whether to use FP16 inference.
        batch_size:           Batch size for VR models.
        use_tta:              Whether to use test-time augmentation.
        music_folder:         Name of the audio folder (under ``audio_files/``).
        input_audio_basename: Basename of the original input audio.
    """
    os.makedirs(store_dir, exist_ok=True)

    no_noise_exists = search_with_word(store_dir, "dry") is not None
    if no_noise_exists:
        logger.info("Noise already removed")
        return

    model_info = get_model_info_by_name(denoise_model)
    logger.info("Removing noise")

    # Resolve the input file from the previous stage
    if input_file is None:
        if deecho:
            input_file = os.path.join(
                now_dir,
                "audio_files",
                music_folder,
                "deecho",
                search_with_word(
                    os.path.join(now_dir, "audio_files", music_folder, "deecho"),
                    "noecho",
                ),
            )
        else:
            input_file = os.path.join(
                now_dir,
                "audio_files",
                music_folder,
                "dereverb",
                search_with_word(
                    os.path.join(now_dir, "audio_files", music_folder, "dereverb"),
                    "noreverb",
                ),
            )

    if (
        model_info["name"] == "Mel-Roformer Denoise Normal by aufr33"
        or model_info["name"] == "Mel-Roformer Denoise Aggressive by aufr33"
    ):
        _ensure_model_files(model_info, use_fp16)
        command = _build_inference_command(
            model_info,
            input_file,
            store_dir,
            devices,
            use_fp16,
        )
        subprocess.run(command)
    else:
        vr_params = _make_vr_params(use_fp16, batch_size, use_tta)
        separator = Separator(
            model_file_dir=os.path.join(now_dir, "models", "denoise"),
            log_level=logging.WARNING,
            normalization_threshold=1.0,
            output_format="flac",
            output_dir=store_dir,
            output_single_stem="No Noise",
            vr_params=vr_params,
        )
        separator.load_model(model_filename=model_info["full_name"])
        separator.separate(input_file)

        # Rename UVR output
        denoise_path = store_dir
        search_result = search_with_two_words(
            denoise_path, input_audio_basename, "No Noise"
        )
        if search_result and "UVR Denoise" in os.path.basename(search_result):
            os.rename(
                os.path.join(denoise_path, search_result),
                os.path.join(
                    denoise_path,
                    f"{input_audio_basename}_dry.flac",
                ),
            )
