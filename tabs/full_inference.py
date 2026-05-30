"""
Full Inference tab for Hyper-RVC WebUI.

UI design based on Applio's inference tab:
https://github.com/IAHispano/Applio

Provides two inference modes:
- **Full Pipeline**: Complete audio processing — vocal separation, karaoke
  separation, dereverb/deecho/denoise, RVC conversion, backing vocals,
  reverb effects, and final mixing.
- **Quick Convert**: Simplified folder-based RVC voice conversion without
  the full separation pipeline.
"""

import datetime
import json
import os
import shutil
import sys
import traceback

import gradio as gr
import regex as re
import torch

from assets.i18n.i18n import I18nAuto
from main.core import full_inference_program
from main.tools.variables import get_f0_methods_ui
from main.rvc.converter import run_rvc_conversion
from main.tools.logger import get_logger
import unicodedata

i18n = I18nAuto()
logger = get_logger(__name__)

now_dir = os.getcwd()
sys.path.append(now_dir)

# ===================================================================
# Path Configuration
# ===================================================================

model_root = os.path.join(now_dir, "logs")
audio_root = os.path.join(now_dir, "audio_files", "original_files")
PRESETS_DIR = os.path.join(now_dir, "assets", "presets")

model_root_relative = os.path.relpath(model_root, now_dir)
audio_root_relative = os.path.relpath(audio_root, now_dir)

os.makedirs(PRESETS_DIR, exist_ok=True)

sup_audioext = {
    "wav", "mp3", "flac", "ogg", "opus", "m4a", "mp4",
    "aac", "alac", "wma", "aiff", "webm", "ac3",
}

# ===================================================================
# Audio Separation Model Names
# ===================================================================

vocals_model_names = [
    "Mel-Roformer by KimberleyJSN",
    "BS-Roformer by ViperX",
    "MDX23C",
]

karaoke_models_names = [
    "Mel-Roformer Karaoke by aufr33 and viperx",
    "UVR-BVE",
]

dereverb_models_names = [
    "MDX23C DeReverb by aufr33 and jarredou",
    "UVR-Deecho-Dereverb",
    "MDX Reverb HQ by FoxJoy",
    "BS-Roformer Dereverb by anvuew",
]

deecho_models_names = [
    "UVR-Deecho-Normal",
    "UVR-Deecho-Aggressive",
]

denoise_models_names = [
    "Mel-Roformer Denoise Normal by aufr33",
    "Mel-Roformer Denoise Aggressive by aufr33",
    "UVR Denoise",
]


# ===================================================================
# File Discovery
# ===================================================================

def get_models():
    """Scan for .pth and .onnx model files, excluding G_/D_ prefixes."""
    return [
        os.path.join(root, file)
        for root, _, files in os.walk(model_root_relative, topdown=False)
        for file in files
        if (
            file.endswith((".pth", ".onnx"))
            and not (file.startswith("G_") or file.startswith("D_"))
        )
    ]


def get_indexes():
    """Scan for .index files, excluding trained indices."""
    return [
        os.path.join(dirpath, filename)
        for dirpath, _, filenames in os.walk(model_root_relative)
        for filename in filenames
        if filename.endswith(".index") and "trained" not in filename
    ]


def get_audio_files():
    """Scan for audio files in the audio root directory."""
    return [
        os.path.join(root, name)
        for root, _, files in os.walk(audio_root_relative, topdown=False)
        for name in files
        if name.endswith(tuple(sup_audioext))
        and root == audio_root_relative
        and "_output" not in name
    ]


# Initial scan
names = get_models()
indexes_list = get_indexes()
audio_paths = get_audio_files()


# ===================================================================
# Model / Index Matching
# ===================================================================

def match_index(model_file_value):
    """Auto-select the best matching index file for a given model.

    Matching priority:
    1. Same folder, exact base-name match
    2. Same folder, any index file
    3. Prefix match across all folders
    4. Substring match across all folders
    """
    if not model_file_value:
        return ""

    model_folder = os.path.dirname(model_file_value)
    model_name = os.path.basename(model_file_value)
    base_name = os.path.splitext(model_name)[0]
    index_files = get_indexes()

    # 1. Same folder + exact base-name
    for idx in index_files:
        if os.path.dirname(idx) == model_folder:
            idx_base = os.path.splitext(os.path.basename(idx))[0]
            if idx_base == base_name:
                return idx

    # 2. Same folder, any index
    for idx in index_files:
        if os.path.dirname(idx) == model_folder:
            return idx

    # 3. Prefix match
    prefix_match = re.match(r"^(.*?)[_\-\.\+]", model_name)
    prefix = prefix_match.group(1) if prefix_match else None
    if prefix:
        for idx in index_files:
            if prefix in os.path.basename(idx):
                return idx

    # 4. Substring / name match
    for idx in index_files:
        if model_name in os.path.basename(idx):
            return idx

    return ""


# ===================================================================
# Speaker ID Extraction
# ===================================================================

def get_speakers_id(model):
    """Extract speaker IDs from a model checkpoint."""
    if model:
        try:
            model_data = torch.load(
                os.path.join(now_dir, model), map_location="cpu", weights_only=True
            )
            speakers_id = model_data.get("speakers_id")
            if speakers_id:
                return list(range(speakers_id))
        except Exception:
            pass
    return [0]


# ===================================================================
# Audio Helpers
# ===================================================================

def output_path_fn(input_audio_path):
    """Generate a default output path next to the input file."""
    if not input_audio_path:
        return ""
    base = os.path.basename(input_audio_path).rsplit(".", 1)[0]
    return os.path.join(os.path.dirname(input_audio_path), f"{base}_output.wav")


def format_title(title):
    """Sanitize a filename for safe filesystem storage."""
    formatted = (
        unicodedata.normalize("NFKD", title)
        .encode("ascii", "ignore")
        .decode("utf-8")
    )
    formatted = re.sub(r"[\u2500-\u257F]+", "", formatted)
    formatted = re.sub(r"[^\w\s.-]", "", formatted)
    formatted = re.sub(r"\s+", "_", formatted)
    return formatted


def save_to_wav(upload_audio):
    """Copy an uploaded audio file into the audio root."""
    file_path = upload_audio
    safe_name = format_title(os.path.basename(file_path))
    target_path = os.path.join(audio_root_relative, safe_name)
    if os.path.exists(target_path):
        os.remove(target_path)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    shutil.copy(file_path, target_path)
    return target_path, output_path_fn(target_path)


def save_to_wav_record(record_button):
    """Save a browser-recorded audio clip into the audio root."""
    if record_button is None:
        return None, None
    new_name = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".wav"
    target_path = os.path.join(audio_root_relative, new_name)
    shutil.move(record_button, target_path)
    return target_path, output_path_fn(target_path)


def delete_outputs():
    """Remove all _output audio files from the audio root."""
    gr.Info(i18n("Outputs cleared!"))
    for root, _, files in os.walk(audio_root_relative, topdown=False):
        for name in files:
            if name.endswith(tuple(sup_audioext)) and "_output" in name:
                os.remove(os.path.join(root, name))


# ===================================================================
# Preset System
# ===================================================================

def list_json_files(directory):
    """Return basenames of JSON files (without .json extension)."""
    if not os.path.isdir(directory):
        return []
    return [f.rsplit(".", 1)[0] for f in os.listdir(directory) if f.endswith(".json")]


def refresh_presets():
    """Refresh the preset dropdown."""
    return gr.update(choices=list_json_files(PRESETS_DIR))


def update_sliders_from_preset(preset):
    """Apply saved preset values to RVC core sliders."""
    try:
        with open(
            os.path.join(PRESETS_DIR, f"{preset}.json"), "r", encoding="utf-8"
        ) as f:
            values = json.load(f)
        return (
            values.get("pitch", 0),
            values.get("index_rate", 0.75),
            values.get("rms_mix_rate", 0.25),
            values.get("protect", 0.33),
        )
    except Exception:
        return gr.update(), gr.update(), gr.update(), gr.update()


def export_presets_button(preset_name, pitch, index_rate, rms_mix_rate, protect):
    """Save current slider values as a named preset JSON."""
    if not preset_name:
        return i18n("Export cancelled")
    path = os.path.join(PRESETS_DIR, f"{preset_name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "pitch": pitch,
            "index_rate": index_rate,
            "rms_mix_rate": rms_mix_rate,
            "protect": protect,
        }, f, ensure_ascii=False, indent=4)
    return i18n("Preset exported successfully!")


# ===================================================================
# Filter & Refresh Helpers
# ===================================================================

def change_choices(model):
    """Refresh model, index, audio, and speaker lists."""
    models = sorted(get_models())
    indexes = sorted(get_indexes())
    audios = sorted(get_audio_files())
    speakers = get_speakers_id(model) if model else [0]
    return (
        {"choices": models, "__type__": "update"},
        {"choices": indexes, "__type__": "update"},
        {"choices": audios, "__type__": "update"},
        {"choices": speakers, "__type__": "update"},
    )


def filter_dropdowns(filter_text):
    """Filter model and index dropdown lists by substring."""
    ft = (filter_text or "").lower()
    return (
        gr.update(choices=[m for m in sorted(get_models()) if ft in m.lower()]),
        gr.update(choices=[i for i in sorted(get_indexes()) if ft in i.lower()]),
    )


def get_number_of_gpus():
    """Return a hyphen-separated string of GPU IDs, or '-' for CPU."""
    if torch.cuda.is_available():
        return "-".join(map(str, range(torch.cuda.device_count())))
    return "-"


# ===================================================================
# Quick Convert — batch folder inference
# ===================================================================

def batch_rvc_program(
    model_path, index_path, input_folder, output_folder,
    pitch, filter_radius, index_rate, rms_mix_rate, protect,
    pitch_extract, embedder_model, split_audio, autotune, hop_length,
    export_format, sid, devices,
):
    """Run RVC conversion on every audio file inside *input_folder*.

    Converted files are written to *output_folder* with an ``_output``
    suffix.  Errors on individual files are logged but do not abort the
    batch.
    """
    if not model_path or not input_folder or not output_folder:
        return i18n("Please fill in all required fields.")

    os.makedirs(output_folder, exist_ok=True)
    processed, errors = 0, 0
    lines = []

    for name in sorted(os.listdir(input_folder)):
        if not name.endswith(tuple(sup_audioext)) or "_output" in name:
            continue
        input_path = os.path.join(input_folder, name)
        base = os.path.splitext(name)[0]
        ext = (export_format or "wav").lower()
        output_path = os.path.join(output_folder, f"{base}_output.{ext}")
        try:
            run_rvc_conversion(
                audio_input_path=input_path,
                audio_output_path=output_path,
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
                hop_length=hop_length,
                export_format=export_format,
            )
            processed += 1
            lines.append(f"  OK: {name} -> {base}_output.{ext}")
        except Exception as exc:
            errors += 1
            lines.append(f"  FAIL: {name} — {str(exc)[:100]}")

    summary = f"Processed: {processed} | Errors: {errors}\n" + "\n".join(lines)
    return summary


# ===================================================================
# Visibility Toggle Helpers
# ===================================================================

def _toggle(cb):
    """Single-component visibility toggle."""
    return gr.update(visible=cb)


def _toggle_n(cb, n):
    """Toggle visibility for *n* components at once."""
    return [gr.update(visible=cb) for _ in range(n)]


# ===================================================================
# Main UI Builder
# ===================================================================

def full_inference_tab():
    """Build and return the full inference interface.

    Layout is modelled on Applio's inference tab:
    https://github.com/IAHispano/Applio/blob/main/tabs/inference/inference.py

    Returns:
        tuple: (model_file, index_file, audio_dropdown) — the shared
        model / index / audio components for cross-tab references.
    """
    default_weight = names[0] if names else None
    default_index = match_index(default_weight) if default_weight else ""

    # ===============================================================
    # 1. Model Selection (shared across both sub-tabs)
    # ===============================================================
    with gr.Column():
        with gr.Row():
            model_file = gr.Dropdown(
                label=i18n("Voice Model"),
                info=i18n("Select the voice model to use for the conversion."),
                choices=sorted(names),
                value=default_weight,
                interactive=True,
                allow_custom_value=True,
            )
            filter_box = gr.Textbox(
                label=i18n("Filter"),
                info=i18n("Path must contain:"),
                placeholder=i18n("Type to filter..."),
                interactive=True,
                scale=0.1,
            )
            index_file = gr.Dropdown(
                label=i18n("Index File"),
                info=i18n("Select the index file to use for the conversion."),
                choices=sorted(indexes_list),
                value=default_index,
                interactive=True,
                allow_custom_value=True,
            )

        with gr.Row():
            unload_button = gr.Button(i18n("Unload Voice"))
            refresh_button = gr.Button(i18n("Refresh"))

            unload_button.click(
                fn=lambda: (
                    {"value": "", "__type__": "update"},
                    {"value": "", "__type__": "update"},
                ),
                inputs=[],
                outputs=[model_file, index_file],
            )

            model_file.select(
                fn=lambda m: match_index(m),
                inputs=[model_file],
                outputs=[index_file],
            )

    # ===============================================================
    # 2. Sub-tabs: Full Pipeline / Quick Convert
    # ===============================================================
    with gr.Tabs():
        # ============================================================
        # SINGLE — Full Pipeline
        # ============================================================
        with gr.Tab(i18n("Full Pipeline")):
            with gr.Column():
                # -- Audio Input --
                upload_audio = gr.Audio(
                    label=i18n("Upload Audio"),
                    type="filepath",
                    editable=False,
                )
                with gr.Row():
                    audio_single = gr.Dropdown(
                        label=i18n("Select Audio"),
                        info=i18n("Select the audio to convert."),
                        choices=sorted(audio_paths),
                        value=audio_paths[0] if audio_paths else "",
                        interactive=True,
                        allow_custom_value=True,
                    )

                # -- Output Display --
                with gr.Row():
                    vc_output1 = gr.Textbox(
                        label=i18n("Output Information"),
                        info=i18n("The output information will be displayed here."),
                    )
                    vc_output2 = gr.Audio(label=i18n("Export Audio"))

                # Hidden output-path field
                output_path = gr.Textbox(visible=False)

                # ---------------------------------------------------
                # Advanced Settings
                # ---------------------------------------------------
                with gr.Accordion(i18n("Advanced Settings"), open=False):
                    with gr.Column():
                        clear_outputs_btn = gr.Button(
                            i18n("Clear Outputs")
                        )
                        export_format_rvc = gr.Radio(
                            label=i18n("Export Format"),
                            info=i18n("Select the format to export the audio."),
                            choices=["WAV", "MP3", "FLAC", "OGG", "M4A"],
                            value="FLAC",
                            interactive=True,
                        )
                        sid_single = gr.Dropdown(
                            label=i18n("Speaker ID"),
                            info=i18n("Select the speaker ID to use for the conversion."),
                            choices=get_speakers_id(default_weight),
                            value=0,
                            interactive=True,
                        )
                        split_audio = gr.Checkbox(
                            label=i18n("Split Audio"),
                            info=i18n("Split the audio into chunks for inference."),
                            value=False,
                            interactive=True,
                        )
                        autotune = gr.Checkbox(
                            label=i18n("Autotune"),
                            info=i18n("Apply soft autotune to inferences."),
                            value=False,
                            interactive=True,
                        )

                # --- RVC Core Parameters ---
                with gr.Accordion(i18n("RVC Settings"), open=False):
                    with gr.Column():
                        pitch = gr.Slider(
                            minimum=-24, maximum=24, step=1,
                            label=i18n("Pitch"),
                            info=i18n("Adjust the pitch of the audio."),
                            value=0, interactive=True,
                        )
                        filter_radius = gr.Slider(
                            minimum=0, maximum=7, step=1,
                            label=i18n("Filter Radius"),
                            info=i18n("Median filtering on tone results."),
                            value=3, interactive=True,
                        )
                        index_rate = gr.Slider(
                            minimum=0, maximum=1,
                            label=i18n("Search Feature Ratio"),
                            info=i18n("Influence of index file."),
                            value=0.75, interactive=True,
                        )
                        rms_mix_rate = gr.Slider(
                            minimum=0, maximum=1,
                            label=i18n("Volume Envelope"),
                            info=i18n("Blend with volume envelope."),
                            value=0.25, interactive=True,
                        )
                        protect = gr.Slider(
                            minimum=0, maximum=0.5,
                            label=i18n("Protect Voiceless Consonants"),
                            info=i18n("Safeguard consonants and breathing."),
                            value=0.33, interactive=True,
                        )
                        pitch_extract = gr.Radio(
                            label=i18n("Pitch Extractor"),
                            info=i18n("Pitch extract algorithm."),
                            choices=get_f0_methods_ui(),
                            value="rmvpe",
                            interactive=True,
                        )
                        hop_length = gr.Slider(
                            minimum=1, maximum=512, step=1,
                            label=i18n("Hop Length"),
                            info=i18n("Hop length for pitch extraction."),
                            value=64,
                            visible=False,
                            interactive=True,
                        )
                        embedder_model = gr.Radio(
                            label=i18n("Embedder Model"),
                            info=i18n("Model used for learning speaker embedding."),
                            choices=[
                                "contentvec",
                                "chinese-hubert-base",
                                "japanese-hubert-base",
                                "korean-hubert-base",
                            ],
                            value="contentvec",
                            interactive=True,
                        )

                # --- Audio Separation ---
                with gr.Accordion(i18n("Audio Separation Settings"), open=False):
                    with gr.Column():
                        with gr.Row():
                            vocal_model = gr.Dropdown(
                                label=i18n("Vocals Model"),
                                info=i18n("Select the vocals model."),
                                choices=sorted(vocals_model_names),
                                value="Mel-Roformer by KimberleyJSN",
                                interactive=True,
                            )
                            karaoke_model = gr.Dropdown(
                                label=i18n("Karaoke Model"),
                                info=i18n("Select the karaoke model."),
                                choices=sorted(karaoke_models_names),
                                value="Mel-Roformer Karaoke by aufr33 and viperx",
                                interactive=True,
                            )
                            dereverb_model = gr.Dropdown(
                                label=i18n("Dereverb Model"),
                                info=i18n("Select the dereverb model."),
                                choices=sorted(dereverb_models_names),
                                value="UVR-Deecho-Dereverb",
                                interactive=True,
                            )
                        with gr.Row():
                            deecho = gr.Checkbox(
                                label=i18n("Deecho"),
                                info=i18n("Apply deecho to the audio."),
                                value=True, interactive=True,
                            )
                            deecho_model = gr.Dropdown(
                                label=i18n("Deecho Model"),
                                info=i18n("Select the deecho model."),
                                choices=sorted(deecho_models_names),
                                value="UVR-Deecho-Normal",
                                interactive=True,
                            )
                        with gr.Row():
                            denoise = gr.Checkbox(
                                label=i18n("Denoise"),
                                info=i18n("Apply denoise to the audio."),
                                value=False, interactive=True,
                            )
                            denoise_model = gr.Dropdown(
                                label=i18n("Denoise Model"),
                                info=i18n("Select the denoise model."),
                                choices=sorted(denoise_models_names),
                                value="Mel-Roformer Denoise Normal by aufr33",
                                visible=False, interactive=True,
                            )
                        with gr.Row():
                            use_tta = gr.Checkbox(
                                label=i18n("Use TTA"),
                                info=i18n("Use Test Time Augmentation."),
                                value=False, interactive=True,
                            )
                            batch_size = gr.Slider(
                                minimum=1, maximum=24, step=1,
                                label=i18n("Batch Size"),
                                info=i18n("Set the batch size for separation."),
                                value=1, interactive=True,
                            )

                # --- Post-Process & Output ---
                with gr.Accordion(i18n("Post-process & Output"), open=False):
                    with gr.Column():
                        with gr.Row():
                            with gr.Column():
                                export_format_final = gr.Radio(
                                    label=i18n("Final Export Format"),
                                    choices=["WAV", "MP3", "FLAC", "OGG", "M4A"],
                                    value="FLAC", interactive=True,
                                )
                                change_inst_pitch = gr.Slider(
                                    label=i18n("Change Instrumental Pitch"),
                                    minimum=-12, maximum=12, step=1,
                                    value=0, interactive=True,
                                )
                                delete_audios = gr.Checkbox(
                                    label=i18n("Delete Intermediate Audios"),
                                    info=i18n("Delete the audios after conversion."),
                                    value=True, interactive=True,
                                )
                            with gr.Column():
                                vocals_volume = gr.Slider(
                                    label=i18n("Vocals Volume"),
                                    info=i18n("Adjust the volume of the vocals."),
                                    minimum=-10, maximum=0, step=1,
                                    value=-3, interactive=True,
                                )
                                instrumentals_volume = gr.Slider(
                                    label=i18n("Instrumentals Volume"),
                                    info=i18n("Adjust the volume of the Instrumentals."),
                                    minimum=-10, maximum=0, step=1,
                                    value=-3, interactive=True,
                                )
                                backing_vocals_volume = gr.Slider(
                                    label=i18n("Backing Vocals Volume"),
                                    info=i18n("Adjust the volume of the backing vocals."),
                                    minimum=-10, maximum=0, step=1,
                                    value=-3, interactive=True,
                                )

                # --- Reverb ---
                with gr.Accordion(i18n("Reverb"), open=False):
                    reverb = gr.Checkbox(
                        label=i18n("Enable Reverb"),
                        info=i18n("Apply reverb to the audio."),
                        value=False, interactive=True,
                    )
                    with gr.Row(visible=False) as reverb_row:
                        reverb_room_size = gr.Slider(
                            minimum=0, maximum=1, step=0.01,
                            label=i18n("Reverb Room Size"),
                            info=i18n("Set the room size of the reverb."),
                            value=0.5, interactive=True,
                        )
                        reverb_damping = gr.Slider(
                            minimum=0, maximum=1, step=0.01,
                            label=i18n("Reverb Damping"),
                            info=i18n("Set the damping of the reverb."),
                            value=0.5, interactive=True,
                        )
                        reverb_wet_gain = gr.Slider(
                            minimum=0, maximum=1, step=0.01,
                            label=i18n("Reverb Wet Gain"),
                            info=i18n("Set the wet gain of the reverb."),
                            value=0.33, interactive=True,
                        )
                        reverb_dry_gain = gr.Slider(
                            minimum=0, maximum=1, step=0.01,
                            label=i18n("Reverb Dry Gain"),
                            info=i18n("Set the dry gain of the reverb."),
                            value=0.4, interactive=True,
                        )
                        reverb_width = gr.Slider(
                            minimum=0, maximum=1, step=0.01,
                            label=i18n("Reverb Width"),
                            info=i18n("Set the width of the reverb."),
                            value=1.0, interactive=True,
                        )

                # --- Preset Settings ---
                with gr.Accordion(i18n("Preset Settings"), open=False):
                    with gr.Row():
                        preset_dropdown = gr.Dropdown(
                            label=i18n("Select Custom Preset"),
                            choices=list_json_files(PRESETS_DIR),
                            interactive=True,
                        )
                        presets_refresh_button = gr.Button(i18n("Refresh Presets"))
                    with gr.Row():
                        preset_name_input = gr.Textbox(
                            label=i18n("Preset Name"),
                            placeholder=i18n("Enter preset name"),
                        )
                        export_button = gr.Button(i18n("Export Preset"))

                # --- Backing Vocals ---
                with gr.Accordion(i18n("Backing Vocals"), open=False):
                    infer_backing_vocals = gr.Checkbox(
                        label=i18n("Infer Backing Vocals"),
                        value=False, interactive=True,
                    )
                    with gr.Row(visible=False) as backing_row:
                        infer_backing_vocals_model = gr.Dropdown(
                            label=i18n("Backing Vocals Model"),
                            choices=sorted(names),
                            value=default_weight,
                            interactive=True,
                            allow_custom_value=False,
                        )
                        infer_backing_vocals_index = gr.Dropdown(
                            label=i18n("Backing Vocals Index"),
                            choices=get_indexes(),
                            value=match_index(default_weight) if default_weight else "",
                            interactive=True,
                            allow_custom_value=True,
                        )

                    infer_backing_vocals_model.select(
                        fn=lambda m: match_index(m),
                        inputs=[infer_backing_vocals_model],
                        outputs=[infer_backing_vocals_index],
                    )

                    with gr.Accordion(
                        i18n("RVC Settings for Backing Vocals"),
                        open=False, visible=False,
                    ) as back_rvc_settings:
                        with gr.Row():
                            with gr.Column():
                                export_format_rvc_back = gr.Radio(
                                    label=i18n("Export Format"),
                                    choices=["WAV", "MP3", "FLAC", "OGG", "M4A"],
                                    value="FLAC", interactive=True,
                                )
                                pitch_back = gr.Slider(
                                    label=i18n("Pitch"),
                                    minimum=-12, maximum=12, step=1,
                                    value=0, interactive=True,
                                )
                                filter_radius_back = gr.Slider(
                                    minimum=0, maximum=7, step=1,
                                    label=i18n("Filter Radius"),
                                    value=3, interactive=True,
                                )
                                split_audio_back = gr.Checkbox(
                                    label=i18n("Split Audio"),
                                    value=False, interactive=True,
                                )
                                autotune_back = gr.Checkbox(
                                    label=i18n("Autotune"),
                                    value=False, interactive=True,
                                )
                            with gr.Column():
                                pitch_extract_back = gr.Radio(
                                    label=i18n("Pitch Extractor"),
                                    choices=get_f0_methods_ui(),
                                    value="rmvpe", interactive=True,
                                )
                                hop_length_back = gr.Slider(
                                    label=i18n("Hop Length"),
                                    minimum=1, maximum=512, step=1,
                                    value=64, visible=False, interactive=True,
                                )
                                embedder_model_back = gr.Radio(
                                    label=i18n("Embedder Model"),
                                    choices=[
                                        "contentvec",
                                        "chinese-hubert-base",
                                        "japanese-hubert-base",
                                        "korean-hubert-base",
                                    ],
                                    value="contentvec", interactive=True,
                                )
                                index_rate_back = gr.Slider(
                                    minimum=0, maximum=1,
                                    label=i18n("Search Feature Ratio"),
                                    value=0.75, interactive=True,
                                )
                                rms_mix_rate_back = gr.Slider(
                                    minimum=0, maximum=1,
                                    label=i18n("Volume Envelope"),
                                    value=0.25, interactive=True,
                                )
                                protect_back = gr.Slider(
                                    minimum=0, maximum=0.5,
                                    label=i18n("Protect Voiceless Consonants"),
                                    value=0.33, interactive=True,
                                )

                # --- Device ---
                with gr.Accordion(i18n("Device"), open=False):
                    devices = gr.Textbox(
                        label=i18n("GPU Devices"),
                        info=i18n(
                            "Device IDs separated by - (e.g. 0-1). Use '-' for CPU."
                        ),
                        value=get_number_of_gpus(),
                        interactive=True,
                    )

            # -- Convert Button --
            convert_button_single = gr.Button(
                i18n("Convert"), variant="primary", size="lg",
            )

        # ============================================================
        # QUICK CONVERT — Batch Folder RVC
        # ============================================================
        with gr.Tab(i18n("Quick Convert")):
            with gr.Column():
                with gr.Row():
                    input_folder_batch = gr.Textbox(
                        label=i18n("Input Folder"),
                        info=i18n("Folder containing audio files to convert."),
                        placeholder=i18n("Enter input path"),
                        value=audio_root,
                        interactive=True,
                    )
                    output_folder_batch = gr.Textbox(
                        label=i18n("Output Folder"),
                        info=i18n("Folder to save converted files."),
                        placeholder=i18n("Enter output path"),
                        value=os.path.join(now_dir, "audio_files", "batch_output"),
                        interactive=True,
                    )

                vc_output3 = gr.Textbox(
                    label=i18n("Output Information"),
                    info=i18n("The output information will be displayed here."),
                )

            with gr.Accordion(i18n("Advanced Settings"), open=False):
                with gr.Column():
                    export_format_batch = gr.Radio(
                        label=i18n("Export Format"),
                        info=i18n("Select the format to export the audio."),
                        choices=["WAV", "MP3", "FLAC", "OGG", "M4A"],
                        value="FLAC", interactive=True,
                    )
                    sid_batch = gr.Dropdown(
                        label=i18n("Speaker ID"),
                        info=i18n("Select the speaker ID to use for the conversion."),
                        choices=get_speakers_id(default_weight),
                        value=0, interactive=True,
                    )
                    split_audio_batch = gr.Checkbox(
                        label=i18n("Split Audio"),
                        info=i18n("Split the audio into chunks for inference."),
                        value=False, interactive=True,
                    )
                    autotune_batch = gr.Checkbox(
                        label=i18n("Autotune"),
                        info=i18n("Apply soft autotune to inferences."),
                        value=False, interactive=True,
                    )
                    pitch_batch = gr.Slider(
                        minimum=-24, maximum=24, step=1,
                        label=i18n("Pitch"),
                        info=i18n("Adjust the pitch of the audio."),
                        value=0, interactive=True,
                    )
                    filter_radius_batch = gr.Slider(
                        minimum=0, maximum=7, step=1,
                        label=i18n("Filter Radius"),
                        info=i18n("Median filtering on tone results."),
                        value=3, interactive=True,
                    )
                    index_rate_batch = gr.Slider(
                        minimum=0, maximum=1,
                        label=i18n("Search Feature Ratio"),
                        info=i18n("Influence of index file."),
                        value=0.75, interactive=True,
                    )
                    rms_mix_rate_batch = gr.Slider(
                        minimum=0, maximum=1,
                        label=i18n("Volume Envelope"),
                        info=i18n("Blend with volume envelope."),
                        value=0.25, interactive=True,
                    )
                    protect_batch = gr.Slider(
                        minimum=0, maximum=0.5,
                        label=i18n("Protect Voiceless Consonants"),
                        info=i18n("Safeguard consonants and breathing."),
                        value=0.33, interactive=True,
                    )
                    pitch_extract_batch = gr.Radio(
                        label=i18n("Pitch Extractor"),
                        info=i18n("Pitch extract algorithm."),
                        choices=get_f0_methods_ui(),
                        value="rmvpe", interactive=True,
                    )
                    hop_length_batch = gr.Slider(
                        minimum=1, maximum=512, step=1,
                        label=i18n("Hop Length"),
                        info=i18n("Hop length for pitch extraction."),
                        value=64, visible=False, interactive=True,
                    )
                    embedder_model_batch = gr.Radio(
                        label=i18n("Embedder Model"),
                        info=i18n("Model used for learning speaker embedding."),
                        choices=[
                            "contentvec",
                            "chinese-hubert-base",
                            "japanese-hubert-base",
                            "korean-hubert-base",
                        ],
                        value="contentvec", interactive=True,
                    )

            convert_button_batch = gr.Button(
                i18n("Convert"), variant="primary", size="lg",
            )

    # ===============================================================
    # 3. Event Handlers — wired up after all components are defined
    # ===============================================================

    # -- Shared: filter, refresh, unload --
    filter_box.blur(
        fn=filter_dropdowns,
        inputs=[filter_box],
        outputs=[model_file, index_file],
    )
    refresh_button.click(
        fn=change_choices,
        inputs=[model_file],
        outputs=[model_file, index_file, audio_single, sid_single],
    )

    # -- Single tab: audio input --
    upload_audio.upload(
        fn=save_to_wav,
        inputs=[upload_audio],
        outputs=[audio_single, output_path],
    )
    upload_audio.stop_recording(
        fn=save_to_wav_record,
        inputs=[upload_audio],
        outputs=[audio_single, output_path],
    )
    audio_single.change(
        fn=output_path_fn,
        inputs=[audio_single],
        outputs=[output_path],
    )
    clear_outputs_btn.click(fn=delete_outputs, inputs=[], outputs=[])

    # -- Presets --
    presets_refresh_button.click(fn=refresh_presets, outputs=[preset_dropdown])
    preset_dropdown.change(
        fn=update_sliders_from_preset,
        inputs=[preset_dropdown],
        outputs=[pitch, index_rate, rms_mix_rate, protect],
    )
    export_button.click(
        fn=export_presets_button,
        inputs=[preset_name_input, pitch, index_rate, rms_mix_rate, protect],
        outputs=[],
    )

    # -- Visibility toggles --
    deecho.change(fn=_toggle, inputs=deecho, outputs=deecho_model)
    denoise.change(fn=_toggle, inputs=denoise, outputs=denoise_model)
    reverb.change(fn=_toggle, inputs=reverb, outputs=reverb_row)

    pitch_extract.change(
        fn=lambda v: gr.update(visible=v in ("crepe", "crepe-tiny", "onnxcrepe")),
        inputs=pitch_extract,
        outputs=hop_length,
    )
    pitch_extract_batch.change(
        fn=lambda v: gr.update(visible=v in ("crepe", "crepe-tiny", "onnxcrepe")),
        inputs=pitch_extract_batch,
        outputs=hop_length_batch,
    )

    def _backing_vis(v):
        return (gr.update(visible=v), gr.update(visible=v), gr.update(visible=v))

    infer_backing_vocals.change(
        fn=_backing_vis,
        inputs=[infer_backing_vocals],
        outputs=[backing_row, back_rvc_settings, infer_backing_vocals_index],
    )

    # -- Single Convert --
    convert_button_single.click(
        fn=full_inference_program,
        inputs=[
            # Must match core.full_inference_program() signature exactly:
            model_file,              # model_path
            index_file,              # index_path
            audio_single,            # input_audio_path
            output_path,             # output_path
            export_format_rvc,       # export_format_rvc
            split_audio,             # split_audio
            autotune,                # autotune
            vocal_model,             # vocal_model
            karaoke_model,           # karaoke_model
            dereverb_model,          # dereverb_model
            deecho,                  # deecho
            deecho_model,            # deecho_model
            denoise,                 # denoise
            denoise_model,           # denoise_model
            reverb,                  # reverb
            vocals_volume,           # vocals_volume
            instrumentals_volume,    # instrumentals_volume
            backing_vocals_volume,    # backing_vocals_volume
            export_format_final,      # export_format_final
            devices,                  # devices
            pitch,                    # pitch
            filter_radius,            # filter_radius
            index_rate,               # index_rate
            rms_mix_rate,             # rms_mix_rate
            protect,                  # protect
            pitch_extract,            # pitch_extract
            hop_length,               # hop_lenght  (note: core.py has a typo)
            reverb_room_size,          # reverb_room_size
            reverb_damping,           # reverb_damping
            reverb_wet_gain,          # reverb_wet_gain
            reverb_dry_gain,          # reverb_dry_gain
            reverb_width,             # reverb_width
            embedder_model,           # embedder_model
            delete_audios,            # delete_audios
            use_tta,                  # use_tta
            batch_size,               # batch_size
            infer_backing_vocals,     # infer_backing_vocals
            infer_backing_vocals_model,  # infer_backing_vocals_model
            infer_backing_vocals_index,  # infer_backing_vocals_index
            change_inst_pitch,         # change_inst_pitch
            pitch_back,                # pitch_back
            filter_radius_back,        # filter_radius_back
            index_rate_back,           # index_rate_back
            rms_mix_rate_back,         # rms_mix_rate_back
            protect_back,              # protect_back
            pitch_extract_back,        # pitch_extract_back
            hop_length_back,           # hop_length_back
            export_format_rvc_back,    # export_format_rvc_back
            split_audio_back,          # split_audio_back
            autotune_back,             # autotune_back
            embedder_model_back,       # embedder_model_back
        ],
        outputs=[vc_output1, vc_output2],
    )

    # -- Batch Convert --
    convert_button_batch.click(
        fn=batch_rvc_program,
        inputs=[
            model_file, index_file,
            input_folder_batch, output_folder_batch,
            pitch_batch, filter_radius_batch,
            index_rate_batch, rms_mix_rate_batch, protect_batch,
            pitch_extract_batch, embedder_model_batch,
            split_audio_batch, autotune_batch, hop_length_batch,
            export_format_batch, sid_batch, devices,
        ],
        outputs=[vc_output3],
    )

    return model_file, index_file, audio_single
