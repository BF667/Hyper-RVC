"""
Core orchestrator for Hyper-RVC.

This module provides the ``full_inference_program`` function which coordinates
the entire audio processing pipeline by calling into the specialised sub-modules:

1. ``main.uvr.separator``  – vocal / karaoke / dereverb / deecho / denoise
2. ``main.rvc.converter``  – RVC voice conversion
3. ``main.tools.audio_utils`` – reverb effects, audio merging

All heavy-lifting is delegated; this module is purely the pipeline coordinator.
"""

import os
import sys
import shutil
from typing import Tuple

import torch
from pydub import AudioSegment

now_dir = os.getcwd()
sys.path.append(now_dir)

from main.tools.variables import check_fp16_support
from main.tools.logger import get_logger

from main.tools.file_utils import (
    search_with_word,
    search_with_two_words,
    get_last_modified_file,
)
from main.tools.audio_utils import add_audio_effects, merge_audios
from main.uvr.separator import (
    separate_vocals,
    separate_karaoke,
    remove_reverb,
    remove_echo,
    remove_noise,
)
from main.rvc.converter import run_rvc_conversion

logger = get_logger(__name__)


def full_inference_program(
    model_path: str,
    index_path: str,
    input_audio_path: str,
    output_path: str,
    export_format_rvc: str,
    split_audio: bool,
    autotune: bool,
    vocal_model: str,
    karaoke_model: str,
    dereverb_model: str,
    deecho: bool,
    deecho_model: str,
    denoise: bool,
    denoise_model: str,
    reverb: bool,
    vocals_volume: float,
    instrumentals_volume: float,
    backing_vocals_volume: float,
    export_format_final: str,
    devices: str,
    pitch: int,
    filter_radius: int,
    index_rate: float,
    rms_mix_rate: float,
    protect: float,
    pitch_extract: str,
    hop_lenght: int,
    reverb_room_size: float,
    reverb_damping: float,
    reverb_wet_gain: float,
    reverb_dry_gain: float,
    reverb_width: float,
    embedder_model: str,
    delete_audios: bool,
    use_tta: bool,
    batch_size: int,
    infer_backing_vocals: bool,
    infer_backing_vocals_model: str,
    infer_backing_vocals_index: str,
    change_inst_pitch: int,
    pitch_back: int,
    filter_radius_back: int,
    index_rate_back: float,
    rms_mix_rate_back: float,
    protect_back: float,
    pitch_extract_back: str,
    hop_length_back: int,
    export_format_rvc_back: str,
    split_audio_back: bool,
    autotune_back: bool,
    embedder_model_back: str,
) -> Tuple[str, str]:
    """
    Run the full RVC inference pipeline on an audio file.

    This function performs:
    1. Vocal separation from the input audio
    2. Karaoke/backing vocal separation
    3. Dereverb processing (optional)
    4. Deecho processing (optional)
    5. Denoise processing (optional)
    6. RVC voice conversion
    7. Backing vocals inference (optional)
    8. Reverb effects (optional)
    9. Pitch adjustment for instrumentals (optional)
    10. Final audio merging

    Returns:
        Tuple of (success message, output file path)
    """
    # Determine device and FP16 support
    if torch.cuda.is_available() and devices != "cpu":
        n_gpu = torch.cuda.device_count()
        devices = devices.replace("-", " ")
        logger.info(f"Number of GPUs available: {n_gpu}")
        first_device = devices.split()[0] if devices.split() else "cuda:0"
        use_fp16 = check_fp16_support(first_device)
        logger.info(f"FP16 inference: {'Enabled' if use_fp16 else 'Disabled'}")
    else:
        devices = "cpu"
        logger.info("Using CPU")
        use_fp16 = False

    music_folder = os.path.splitext(os.path.basename(input_audio_path))[0]
    input_audio_basename = os.path.splitext(os.path.basename(input_audio_path))[0]

    # ------------------------------------------------------------------
    # 1. Vocal separation
    # ------------------------------------------------------------------
    store_dir = os.path.join(now_dir, "audio_files", music_folder, "vocals")
    inst_dir = os.path.join(now_dir, "audio_files", music_folder, "instrumentals")
    inst_file = separate_vocals(
        input_audio_path, vocal_model, store_dir, inst_dir, devices, use_fp16
    )
    if inst_file is None:
        logger.error(
            "Vocal separation failed — instrumental file was not produced. "
            "Check that the vocal separation model downloaded correctly and "
            "that the input audio is valid."
        )
        raise RuntimeError(
            "Vocal separation did not produce an instrumental file. "
            "See the log for details."
        )

    # ------------------------------------------------------------------
    # 2. Karaoke separation
    # ------------------------------------------------------------------
    store_dir = os.path.join(now_dir, "audio_files", music_folder, "karaoke")
    vocals_path = os.path.join(now_dir, "audio_files", music_folder, "vocals")
    input_file = search_with_word(vocals_path, "vocals")
    if input_file:
        input_file = os.path.join(vocals_path, input_file)
    separate_karaoke(
        input_file, karaoke_model, store_dir, devices, use_fp16,
        batch_size, use_tta, input_audio_basename
    )

    # ------------------------------------------------------------------
    # 3. Dereverb
    # ------------------------------------------------------------------
    store_dir = os.path.join(now_dir, "audio_files", music_folder, "dereverb")
    karaoke_path = os.path.join(now_dir, "audio_files", music_folder, "karaoke")
    input_file = search_with_word(karaoke_path, "karaoke")
    if input_file:
        input_file = os.path.join(karaoke_path, input_file)
    remove_reverb(
        input_file, dereverb_model, store_dir, devices, use_fp16,
        batch_size, use_tta, input_audio_basename
    )

    # ------------------------------------------------------------------
    # 4. Deecho (optional)
    # ------------------------------------------------------------------
    store_dir = os.path.join(now_dir, "audio_files", music_folder, "deecho")
    if deecho:
        dereverb_path = os.path.join(now_dir, "audio_files", music_folder, "dereverb")
        noreverb_file = search_with_word(dereverb_path, "noreverb")
        deecho_input = os.path.join(dereverb_path, noreverb_file)
        remove_echo(
            deecho_input, deecho_model, store_dir, devices, use_fp16,
            batch_size, use_tta, input_audio_basename
        )

    # ------------------------------------------------------------------
    # 5. Denoise (optional)
    # ------------------------------------------------------------------
    store_dir = os.path.join(now_dir, "audio_files", music_folder, "denoise")
    if denoise:
        remove_noise(
            input_file=None,
            denoise_model=denoise_model,
            store_dir=store_dir,
            deecho=deecho,
            devices=devices,
            use_fp16=use_fp16,
            batch_size=batch_size,
            use_tta=use_tta,
            music_folder=music_folder,
            input_audio_basename=input_audio_basename,
        )

    # ------------------------------------------------------------------
    # 6. RVC voice conversion
    # ------------------------------------------------------------------
    denoise_path = os.path.join(now_dir, "audio_files", music_folder, "denoise")
    deecho_path = os.path.join(now_dir, "audio_files", music_folder, "deecho")
    dereverb_path = os.path.join(now_dir, "audio_files", music_folder, "dereverb")

    denoise_audio = search_with_two_words(
        denoise_path, input_audio_basename, "dry"
    )
    deecho_audio = search_with_two_words(
        deecho_path, input_audio_basename, "noecho"
    )
    dereverb = search_with_two_words(
        dereverb_path, input_audio_basename, "noreverb"
    )

    if denoise_audio:
        final_path = os.path.join(denoise_path, denoise_audio)
    elif deecho_audio:
        final_path = os.path.join(deecho_path, deecho_audio)
    elif dereverb:
        final_path = os.path.join(dereverb_path, dereverb)
    else:
        final_path = None

    store_dir = os.path.join(now_dir, "audio_files", music_folder, "rvc")
    os.makedirs(store_dir, exist_ok=True)
    output_rvc = os.path.join(store_dir, f"{input_audio_basename}_rvc.wav")

    run_rvc_conversion(
        audio_input_path=final_path,
        audio_output_path=output_rvc,
        model_path=model_path,
        index_path=index_path,
        embedder_model=embedder_model,
        pitch=pitch,
        f0_method=pitch_extract,
        filter_radius=filter_radius,
        index_rate=index_rate,
        volume_envelope=rms_mix_rate,
        protect=protect,
        split_audio=split_audio,
        f0_autotune=autotune,
        hop_length=hop_lenght,
        export_format=export_format_rvc,
    )

    backing_vocals = os.path.join(
        karaoke_path, search_with_word(karaoke_path, "instrumental")
    )

    # ------------------------------------------------------------------
    # 7. Backing vocals inference (optional)
    # ------------------------------------------------------------------
    if infer_backing_vocals:
        logger.info("Inferring backing vocals")
        karaoke_path = os.path.join(now_dir, "audio_files", music_folder, "karaoke")
        instrumental_file = search_with_word(karaoke_path, "instrumental")
        backing_vocals = os.path.join(karaoke_path, instrumental_file)
        output_backing_vocals = os.path.join(
            karaoke_path, f"{input_audio_basename}_instrumental_output.wav"
        )
        run_rvc_conversion(
            audio_input_path=backing_vocals,
            audio_output_path=output_backing_vocals,
            model_path=infer_backing_vocals_model,
            index_path=infer_backing_vocals_index,
            embedder_model=embedder_model_back,
            pitch=pitch_back,
            f0_method=pitch_extract_back,
            filter_radius=filter_radius_back,
            index_rate=index_rate_back,
            volume_envelope=rms_mix_rate_back,
            protect=protect_back,
            split_audio=split_audio_back,
            f0_autotune=autotune_back,
            hop_length=hop_length_back,
            export_format=export_format_rvc_back,
        )
        backing_vocals = output_backing_vocals

    # ------------------------------------------------------------------
    # 8. Post-process – reverb (optional)
    # ------------------------------------------------------------------
    if reverb:
        rvc_dir = os.path.join(now_dir, "audio_files", music_folder, "rvc")
        reverb_input = os.path.join(
            rvc_dir, get_last_modified_file(rvc_dir)
        )
        reverb_output = os.path.join(rvc_dir, os.path.basename(input_audio_path))
        add_audio_effects(
            reverb_input, reverb_room_size, reverb_wet_gain, reverb_dry_gain,
            reverb_damping, reverb_width, reverb_output
        )

    # ------------------------------------------------------------------
    # 9. Pitch adjustment for instrumentals (optional)
    # ------------------------------------------------------------------
    if change_inst_pitch != 0:
        logger.info("Changing instrumental pitch")
        inst_path_dir = os.path.join(
            now_dir, "audio_files", music_folder, "instrumentals"
        )
        inst_file_name = search_with_word(inst_path_dir, "instrumentals")
        inst_path_file = os.path.join(inst_path_dir, inst_file_name)
        audio = AudioSegment.from_file(inst_path_file)
        factor = 2 ** (change_inst_pitch / 12)
        new_frame_rate = int(audio.frame_rate * factor)
        audio = audio._spawn(audio.raw_data, overrides={"frame_rate": new_frame_rate})
        audio = audio.set_frame_rate(audio.frame_rate)
        audio.export(os.path.join(inst_path_dir, "inst_with_changed_pitch.flac"), format="flac")

    # ------------------------------------------------------------------
    # 10. Merge audios
    # ------------------------------------------------------------------
    store_dir = os.path.join(now_dir, "audio_files", music_folder, "final")
    os.makedirs(store_dir, exist_ok=True)

    vocals_path = os.path.join(now_dir, "audio_files", music_folder, "rvc")
    vocals_file = get_last_modified_file(vocals_path)
    vocals_file = os.path.join(vocals_path, vocals_file)

    karaoke_path = os.path.join(now_dir, "audio_files", music_folder, "karaoke")
    karaoke_file = search_with_word(karaoke_path, "Instrumental") or search_with_word(
        karaoke_path, "instrumental"
    )
    karaoke_file = os.path.join(karaoke_path, karaoke_file)

    final_output_path = os.path.join(
        store_dir,
        f"{input_audio_basename}_final.{export_format_final.lower()}",
    )
    logger.info("Merging audios")
    result = merge_audios(
        vocals_file, inst_file, backing_vocals, final_output_path,
        vocals_volume, instrumentals_volume, backing_vocals_volume,
        export_format_final,
    )
    logger.info("Audios merged!")

    # ------------------------------------------------------------------
    # Cleanup intermediate files
    # ------------------------------------------------------------------
    if delete_audios:
        main_directory = os.path.join(now_dir, "audio_files", music_folder)
        folder_to_keep = "final"
        for folder_name in os.listdir(main_directory):
            folder_path = os.path.join(main_directory, folder_name)
            if os.path.isdir(folder_path) and folder_name != folder_to_keep:
                shutil.rmtree(folder_path)

    return (
        f"Audio file {input_audio_basename} converted with success",
        result,
    )
