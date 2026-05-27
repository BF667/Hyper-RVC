from main.core import full_inference_program
import sys, os
import gradio as gr
import regex as re
from assets.i18n.i18n import I18nAuto
import torch
import shutil
import unicodedata

i18n = I18nAuto()

now_dir = os.getcwd()
sys.path.append(now_dir)

from main.tools.variables import get_f0_methods_ui

model_root = os.path.join(now_dir, "logs")
audio_root = os.path.join(now_dir, "audio_files", "original_files")

model_root_relative = os.path.relpath(model_root, now_dir)
audio_root_relative = os.path.relpath(audio_root, now_dir)

sup_audioext = {
    "wav", "mp3", "flac", "ogg", "opus", "m4a", "mp4", "aac",
    "alac", "wma", "aiff", "webm", "ac3"
}

names = [
    os.path.join(root, file)
    for root, _, files in os.walk(model_root_relative, topdown=False)
    for file in files
    if (
        file.endswith((".pth", ".onnx"))
        and not (file.startswith("G_") or file.startswith("D_"))
    )
]

indexes_list = [
    os.path.join(root, name)
    for root, _, files in os.walk(model_root_relative, topdown=False)
    for name in files
    if name.endswith(".index") and "trained" not in name
]

audio_paths = [
    os.path.join(root, name)
    for root, _, files in os.walk(audio_root_relative, topdown=False)
    for name in files
    if name.endswith(tuple(sup_audioext))
    and root == audio_root_relative
    and "_output" not in name
]

vocals_model_names = [
    "Mel-Roformer by KimberleyJSN",
    "BS-Roformer by ViperX",
    "MDX23C",
]

karaoke_models_names = [
    "Mel-Roformer Karaoke by aufr33 and viperx",
    "UVR-BVE",
]

denoise_models_names = [
    "Mel-Roformer Denoise Normal by aufr33",
    "Mel-Roformer Denoise Aggressive by aufr33",
    "UVR Denoise",
]

dereverb_models_names = [
    "MDX23C DeReverb by aufr33 and jarredou",
    "UVR-Deecho-Dereverb",
    "MDX Reverb HQ by FoxJoy",
    "BS-Roformer Dereverb by anvuew",
]

deecho_models_names = ["UVR-Deecho-Normal", "UVR-Deecho-Aggressive"]


def get_indexes():
    indexes_list = [
        os.path.join(dirpath, filename)
        for dirpath, _, filenames in os.walk(model_root_relative)
        for filename in filenames
        if filename.endswith(".index") and "trained" not in filename
    ]
    return indexes_list if indexes_list else ""


def match_index(model_file_value):
    if model_file_value:
        model_folder = os.path.dirname(model_file_value)
        model_name = os.path.basename(model_file_value)
        index_files = get_indexes()
        pattern = r"^(.*?)_"
        match = re.match(pattern, model_name)
        for index_file in index_files:
            if os.path.dirname(index_file) == model_folder:
                return index_file
            elif match and match.group(1) in os.path.basename(index_file):
                return index_file
            elif model_name in os.path.basename(index_file):
                return index_file
    return ""


def output_path_fn(input_audio_path):
    original_name_without_extension = os.path.basename(input_audio_path).rsplit(".", 1)[0]
    new_name = original_name_without_extension + "_output.wav"
    output_path = os.path.join(os.path.dirname(input_audio_path), new_name)
    return output_path


def get_number_of_gpus():
    if torch.cuda.is_available():
        num_gpus = torch.cuda.device_count()
        return "-".join(map(str, range(num_gpus)))
    else:
        return "-"


def max_vram_gpu(gpu):
    if torch.cuda.is_available():
        gpu_properties = torch.cuda.get_device_properties(gpu)
        total_memory_gb = round(gpu_properties.total_memory / 1024 / 1024 / 1024)
        return total_memory_gb / 2
    else:
        return "0"


def format_title(title):
    formatted_title = (
        unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("utf-8")
    )
    formatted_title = re.sub(r"[\u2500-\u257F]+", "", formatted_title)
    formatted_title = re.sub(r"[^\w\s.-]", "", formatted_title)
    formatted_title = re.sub(r"\s+", "_", formatted_title)
    return formatted_title


def save_to_wav(upload_audio):
    file_path = upload_audio
    formated_name = format_title(os.path.basename(file_path))
    target_path = os.path.join(audio_root_relative, formated_name)

    if os.path.exists(target_path):
        os.remove(target_path)

    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    shutil.copy(file_path, target_path)
    return target_path, output_path_fn(target_path)


def delete_outputs():
    gr.Info(f"Outputs cleared!")
    for root, _, files in os.walk(audio_root_relative, topdown=False):
        for name in files:
            if name.endswith(tuple(sup_audioext)) and name.__contains__("_output"):
                os.remove(os.path.join(root, name))


def change_choices():
    names = [
        os.path.join(root, file)
        for root, _, files in os.walk(model_root_relative, topdown=False)
        for file in files
        if (
            file.endswith((".pth", ".onnx"))
            and not (file.startswith("G_") or file.startswith("D_"))
        )
    ]

    indexes_list = [
        os.path.join(root, name)
        for root, _, files in os.walk(model_root_relative, topdown=False)
        for name in files
        if name.endswith(".index") and "trained" not in name
    ]

    audio_paths = [
        os.path.join(root, name)
        for root, _, files in os.walk(audio_root_relative, topdown=False)
        for name in files
        if name.endswith(tuple(sup_audioext))
        and root == audio_root_relative
        and "_output" not in name
    ]

    return (
        {"choices": sorted(names), "__type__": "update"},
        {"choices": sorted(indexes_list), "__type__": "update"},
        {"choices": sorted(audio_paths), "__type__": "update"},
    )


def full_inference_tab():
    default_weight = names[0] if names else None

    # -- Voice Model --
    with gr.Row():
        model_file = gr.Dropdown(
            label=i18n("Voice Model"),
            info=i18n("Select the voice model (.pth / .onnx)."),
            choices=sorted(names, key=lambda path: os.path.getsize(path)),
            interactive=True,
            value=default_weight,
            allow_custom_value=True,
        )
        index_file = gr.Dropdown(
            label=i18n("Index File"),
            info=i18n("Select the index file (.index)."),
            choices=get_indexes(),
            value=match_index(default_weight) if default_weight else "",
            interactive=True,
            allow_custom_value=True,
        )

    model_file.select(
        fn=lambda model_file_value: match_index(model_file_value),
        inputs=[model_file],
        outputs=[index_file],
    )

    # -- Audio Input --
    upload_audio = gr.Audio(
        label=i18n("Upload Audio"),
        type="filepath",
        editable=False,
        sources="upload",
    )
    audio = gr.Dropdown(
        label=i18n("Select Audio"),
        info=i18n("Pick from existing files."),
        choices=sorted(audio_paths),
        value=audio_paths[0] if audio_paths else "",
        interactive=True,
        allow_custom_value=True,
    )

    # -- Output --
    vc_output1 = gr.Textbox(
        label=i18n("Output Status"),
        interactive=False,
        lines=2,
    )
    vc_output2 = gr.Audio(
        label=i18n("Result"),
        type="numpy",
    )

    # Hidden output path
    output_path = gr.Textbox(visible=False)

    # -- Advanced Settings --
    with gr.Accordion(i18n("Advanced Settings"), open=False):

        # RVC Settings
        with gr.Accordion(i18n("RVC Settings"), open=False):
            with gr.Row():
                with gr.Column():
                    export_format_rvc = gr.Radio(
                        label=i18n("Export Format"),
                        choices=["WAV", "MP3", "FLAC", "OGG", "M4A"],
                        value="FLAC",
                        interactive=True,
                    )
                    pitch = gr.Slider(
                        label=i18n("Pitch"),
                        info=i18n("Adjust pitch (semitones)."),
                        minimum=-12, maximum=12, step=1, value=0,
                        interactive=True,
                    )
                    filter_radius = gr.Slider(
                        minimum=0, maximum=7,
                        label=i18n("Filter Radius"),
                        info=i18n("Median filtering on tone results."),
                        value=3, step=1, interactive=True,
                    )
                    split_audio = gr.Checkbox(
                        label=i18n("Split Audio"),
                        value=False, interactive=True,
                    )
                    autotune = gr.Checkbox(
                        label=i18n("Autotune"),
                        value=False, interactive=True,
                    )

                with gr.Column():
                    pitch_extract = gr.Radio(
                        label=i18n("Pitch Extractor"),
                        info=i18n("Pitch extract algorithm."),
                        choices=get_f0_methods_ui(),
                        value="rmvpe",
                        interactive=True,
                    )
                    hop_length = gr.Slider(
                        label=i18n("Hop Length"),
                        minimum=1, maximum=512, step=1, value=64,
                        visible=False, interactive=True,
                    )
                    embedder_model = gr.Radio(
                        label=i18n("Embedder Model"),
                        choices=["contentvec", "chinese-hubert-base", "japanese-hubert-base", "korean-hubert-base"],
                        value="contentvec",
                        interactive=True,
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
                        value=0.33, interactive=True,
                    )

        # Audio Separation Settings
        with gr.Accordion(i18n("Audio Separation"), open=False):
            with gr.Row():
                vocal_model = gr.Dropdown(
                    label=i18n("Vocals Model"),
                    choices=sorted(vocals_model_names),
                    value="Mel-Roformer by KimberleyJSN",
                    interactive=True,
                )
                karaoke_model = gr.Dropdown(
                    label=i18n("Karaoke Model"),
                    choices=sorted(karaoke_models_names),
                    value="Mel-Roformer Karaoke by aufr33 and viperx",
                    interactive=True,
                )
                dereverb_model = gr.Dropdown(
                    label=i18n("Dereverb Model"),
                    choices=sorted(dereverb_models_names),
                    value="UVR-Deecho-Dereverb",
                    interactive=True,
                )
            with gr.Row():
                deecho = gr.Checkbox(
                    label=i18n("Deecho"), value=True, interactive=True,
                )
                deecho_model = gr.Dropdown(
                    label=i18n("Deecho Model"),
                    choices=sorted(deecho_models_names),
                    value="UVR-Deecho-Normal",
                    interactive=True,
                )
            with gr.Row():
                denoise = gr.Checkbox(
                    label=i18n("Denoise"), value=False, interactive=True,
                )
                denoise_model = gr.Dropdown(
                    label=i18n("Denoise Model"),
                    choices=sorted(denoise_models_names),
                    value="Mel-Roformer Denoise Normal by aufr33",
                    visible=False, interactive=True,
                )
            with gr.Row():
                use_tta = gr.Checkbox(
                    label=i18n("Use TTA"), value=False, interactive=True,
                )
                batch_size = gr.Slider(
                    minimum=1, maximum=24, step=1,
                    label=i18n("Batch Size"), value=1, interactive=True,
                )

        # Post-process Settings
        with gr.Accordion(i18n("Post-process & Output"), open=False):
            with gr.Row():
                with gr.Column():
                    export_format_final = gr.Radio(
                        label=i18n("Final Export Format"),
                        choices=["WAV", "MP3", "FLAC", "OGG", "M4A"],
                        value="FLAC", interactive=True,
                    )
                    change_inst_pitch = gr.Slider(
                        label=i18n("Change Instrumental Pitch"),
                        minimum=-12, maximum=12, step=1, value=0,
                        interactive=True,
                    )
                    delete_audios = gr.Checkbox(
                        label=i18n("Delete Intermediate Audios"),
                        value=True, interactive=True,
                    )
                with gr.Column():
                    vocals_volume = gr.Slider(
                        label=i18n("Vocals Volume"),
                        minimum=-10, maximum=0, step=1, value=-3,
                        interactive=True,
                    )
                    instrumentals_volume = gr.Slider(
                        label=i18n("Instrumentals Volume"),
                        minimum=-10, maximum=0, step=1, value=-3,
                        interactive=True,
                    )
                    backing_vocals_volume = gr.Slider(
                        label=i18n("Backing Vocals Volume"),
                        minimum=-10, maximum=0, step=1, value=-3,
                        interactive=True,
                    )

            # Reverb
            with gr.Accordion(i18n("Reverb"), open=False):
                reverb = gr.Checkbox(
                    label=i18n("Enable Reverb"), value=False, interactive=True,
                )
                with gr.Row(visible=False) as reverb_row:
                    reverb_room_size = gr.Slider(minimum=0, maximum=1, label=i18n("Room Size"), value=0.5, interactive=True)
                    reverb_damping = gr.Slider(minimum=0, maximum=1, label=i18n("Damping"), value=0.5, interactive=True)
                    reverb_wet_gain = gr.Slider(minimum=0, maximum=1, label=i18n("Wet Gain"), value=0.33, interactive=True)
                    reverb_dry_gain = gr.Slider(minimum=0, maximum=1, label=i18n("Dry Gain"), value=0.4, interactive=True)
                    reverb_width = gr.Slider(minimum=0, maximum=1, label=i18n("Width"), value=1.0, interactive=True)

        # Backing Vocals
        with gr.Accordion(i18n("Backing Vocals"), open=False):
            infer_backing_vocals = gr.Checkbox(
                label=i18n("Infer Backing Vocals"),
                value=False, interactive=True,
            )

            with gr.Row(visible=False) as backing_row:
                infer_backing_vocals_model = gr.Dropdown(
                    label=i18n("Backing Vocals Model"),
                    choices=sorted(names, key=lambda path: os.path.getsize(path)),
                    interactive=True,
                    value=default_weight,
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
                    fn=lambda model_file_value: match_index(model_file_value),
                    inputs=[infer_backing_vocals_model],
                    outputs=[infer_backing_vocals_index],
                )

            with gr.Accordion(i18n("RVC Settings for Backing Vocals"), open=False, visible=False) as back_rvc_settings:
                with gr.Row():
                    with gr.Column():
                        export_format_rvc_back = gr.Radio(
                            label=i18n("Export Format"),
                            choices=["WAV", "MP3", "FLAC", "OGG", "M4A"],
                            value="FLAC", interactive=True,
                        )
                        pitch_back = gr.Slider(
                            label=i18n("Pitch"),
                            minimum=-12, maximum=12, step=1, value=0,
                            interactive=True,
                        )
                        filter_radius_back = gr.Slider(
                            minimum=0, maximum=7,
                            label=i18n("Filter Radius"), value=3, step=1,
                            interactive=True,
                        )
                        split_audio_back = gr.Checkbox(label=i18n("Split Audio"), value=False, interactive=True)
                        autotune_back = gr.Checkbox(label=i18n("Autotune"), value=False, interactive=True)
                    with gr.Column():
                        pitch_extract_back = gr.Radio(
                            label=i18n("Pitch Extractor"),
                            choices=get_f0_methods_ui(), value="rmvpe",
                            interactive=True,
                        )
                        hop_length_back = gr.Slider(
                            label=i18n("Hop Length"),
                            minimum=1, maximum=512, step=1, value=64,
                            visible=False, interactive=True,
                        )
                        embedder_model_back = gr.Radio(
                            label=i18n("Embedder Model"),
                            choices=["contentvec", "chinese-hubert-base", "japanese-hubert-base", "korean-hubert-base"],
                            value="contentvec", interactive=True,
                        )
                        index_rate_back = gr.Slider(
                            minimum=0, maximum=1,
                            label=i18n("Search Feature Ratio"), value=0.75,
                            interactive=True,
                        )
                        rms_mix_rate_back = gr.Slider(
                            minimum=0, maximum=1,
                            label=i18n("Volume Envelope"), value=0.25,
                            interactive=True,
                        )
                        protect_back = gr.Slider(
                            minimum=0, maximum=0.5,
                            label=i18n("Protect Voiceless Consonants"), value=0.33,
                            interactive=True,
                        )

        # Device
        with gr.Accordion(i18n("Device"), open=False):
            devices = gr.Textbox(
                label=i18n("GPU Devices"),
                info=i18n("Device IDs separated by - (e.g. 0-1). Use '-' for CPU."),
                value=get_number_of_gpus(),
                interactive=True,
            )

    # -- Event Handlers --
    upload_audio.upload(
        fn=save_to_wav,
        inputs=[upload_audio],
        outputs=[audio, output_path],
    )

    # -- Action Buttons --
    with gr.Row():
        convert_button = gr.Button(
            i18n("Convert"),
            variant="primary",
            size="lg",
        )
        refresh_button = gr.Button(
            i18n("Refresh"),
            size="lg",
        )
        unload_button = gr.Button(
            i18n("Unload Model"),
            size="lg",
        )
        clear_button = gr.Button(
            i18n("Clear Outputs"),
            variant="stop",
            size="lg",
        )

    convert_button.click(
        full_inference_program,
        inputs=[
            model_file,
            index_file,
            audio,
            output_path,
            export_format_rvc,
            split_audio,
            autotune,
            vocal_model,
            karaoke_model,
            dereverb_model,
            deecho,
            deecho_model,
            denoise,
            denoise_model,
            reverb,
            vocals_volume,
            instrumentals_volume,
            backing_vocals_volume,
            export_format_final,
            devices,
            pitch,
            filter_radius,
            index_rate,
            rms_mix_rate,
            protect,
            pitch_extract,
            hop_length,
            reverb_room_size,
            reverb_damping,
            reverb_wet_gain,
            reverb_dry_gain,
            reverb_width,
            embedder_model,
            delete_audios,
            use_tta,
            batch_size,
            infer_backing_vocals,
            infer_backing_vocals_model,
            infer_backing_vocals_index,
            change_inst_pitch,
            pitch_back,
            filter_radius_back,
            index_rate_back,
            rms_mix_rate_back,
            protect_back,
            pitch_extract_back,
            hop_length_back,
            export_format_rvc_back,
            split_audio_back,
            autotune_back,
            embedder_model_back,
        ],
        outputs=[vc_output1, vc_output2],
    )

    refresh_button.click(
        fn=change_choices,
        inputs=[],
        outputs=[model_file, index_file, audio],
    )

    def unload_model():
        gr.Info("Model unloaded.")
        return (
            gr.update(value=None),
            gr.update(value=""),
        )

    unload_button.click(
        fn=unload_model,
        inputs=[],
        outputs=[model_file, index_file],
    )

    clear_button.click(
        fn=lambda: (delete_outputs(), gr.update(value=""), gr.update(value=None)),
        inputs=[],
        outputs=[vc_output1, vc_output2],
    )

    # Visibility toggles
    deecho.change(fn=lambda c: gr.update(visible=c), inputs=deecho, outputs=deecho_model)
    denoise.change(fn=lambda c: gr.update(visible=c), inputs=denoise, outputs=denoise_model)
    reverb.change(fn=lambda c: gr.update(visible=c), inputs=reverb, outputs=reverb_row)

    def update_visibility_infer_backing(v):
        return (
            gr.update(visible=v), gr.update(visible=v), gr.update(visible=v),
        )
    infer_backing_vocals.change(
        fn=update_visibility_infer_backing,
        inputs=[infer_backing_vocals],
        outputs=[backing_row, back_rvc_settings, infer_backing_vocals_index],
    )

    pitch_extract.change(
        fn=lambda v: gr.update(visible=v in ["crepe", "crepe-tiny", "onnxcrepe"]),
        inputs=pitch_extract, outputs=hop_length,
    )

    return model_file, index_file, audio
