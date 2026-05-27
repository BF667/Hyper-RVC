"""
Realtime Voice Conversion tab for Hyper-RVC WebUI.

Server-mode only: uses sounddevice for audio I/O and the existing
RVC pipeline for voice conversion. No UVR/audio separation.

Based on concepts from deiteris/voice-changer and Vietnamese-RVC,
with a simpler single-file architecture.
"""

import os
import sys
import time
import torch
import threading

import gradio as gr

now_dir = os.getcwd()
sys.path.append(now_dir)

from assets.i18n.i18n import I18nAuto
from main.tools.variables import get_f0_methods_ui

i18n = I18nAuto()

# Check sounddevice availability
try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except (ImportError, OSError):
    HAS_SOUNDDEVICE = False

# -- Model scanning --

model_root = os.path.join(now_dir, "logs")
model_root_relative = os.path.relpath(model_root, now_dir)


def get_model_files():
    return sorted([
        os.path.join(root, file)
        for root, _, files in os.walk(model_root_relative, topdown=False)
        for file in files
        if (
            file.endswith((".pth", ".onnx"))
            and not (file.startswith("G_") or file.startswith("D_"))
        )
    ], key=lambda path: os.path.getsize(path))


def get_index_files():
    return sorted([
        os.path.join(root, name)
        for root, _, files in os.walk(model_root_relative, topdown=False)
        for name in files
        if name.endswith(".index") and "trained" not in name
    ])


def get_audio_devices():
    """Return device lists for Gradio dropdowns."""
    if not HAS_SOUNDDEVICE:
        return [], []

    devices = sd.query_devices()
    inputs = []
    outputs = []
    for i, dev in enumerate(devices):
        name = dev["name"]
        if dev["max_input_channels"] > 0:
            inputs.append(name)
        if dev["max_output_channels"] > 0:
            outputs.append(name)
    return inputs, outputs


# -- Global state --

engine = None
running = False
status_thread = None


def realtime_tab():
    """Create the Realtime Voice Conversion tab."""

    models = get_model_files()
    indexes = get_index_files()
    default_model = models[0] if models else None
    input_devs, output_devs = get_audio_devices()
    default_input = input_devs[0] if input_devs else None
    default_output = output_devs[0] if output_devs else None

    # -- Model Selection --
    gr.Markdown(
        "### Voice Model\n"
        "Select a voice model and optional index file to start realtime voice conversion. "
        "Audio is captured from your microphone and converted output plays through your speakers."
    )

    with gr.Row():
        model_file = gr.Dropdown(
            label=i18n("Voice Model"),
            info=i18n("RVC model (.pth / .onnx)."),
            choices=models,
            value=default_model,
            interactive=True,
            allow_custom_value=True,
        )
        index_file = gr.Dropdown(
            label=i18n("Index File"),
            info=i18n("Optional index file (.index)."),
            choices=indexes,
            value=indexes[0] if indexes else "",
            interactive=True,
            allow_custom_value=True,
        )

    # -- RVC Settings --
    with gr.Accordion(i18n("RVC Settings"), open=False):
        with gr.Row():
            with gr.Column():
                pitch = gr.Slider(
                    label=i18n("Pitch"),
                    info=i18n("Pitch shift in semitones."),
                    minimum=-12, maximum=12, step=1, value=0,
                    interactive=True,
                )
                index_rate = gr.Slider(
                    minimum=0, maximum=1,
                    label=i18n("Search Feature Ratio"),
                    info=i18n("Influence of index file."),
                    value=0.75, interactive=True,
                )
                protect = gr.Slider(
                    minimum=0, maximum=0.5,
                    label=i18n("Protect Voiceless Consonants"),
                    value=0.33, interactive=True,
                )
                filter_radius = gr.Slider(
                    minimum=0, maximum=7,
                    label=i18n("Filter Radius"),
                    info=i18n("Median filtering on tone results."),
                    value=3, step=1, interactive=True,
                )
                silence_threshold = gr.Slider(
                    minimum=0, maximum=0.05,
                    label=i18n("Silence Threshold"),
                    info=i18n("RMS below this is treated as silence."),
                    value=0.001, step=0.001, interactive=True,
                )
            with gr.Column():
                pitch_extract = gr.Radio(
                    label=i18n("Pitch Extractor"),
                    info=i18n("Pitch extract algorithm."),
                    choices=get_f0_methods_ui(),
                    value="rmvpe",
                    interactive=True,
                )
                embedder_model = gr.Radio(
                    label=i18n("Embedder Model"),
                    choices=["contentvec", "chinese-hubert-base", "japanese-hubert-base", "korean-hubert-base"],
                    value="contentvec",
                    interactive=True,
                )
                autotune = gr.Checkbox(
                    label=i18n("Autotune"),
                    value=False, interactive=True,
                )

    # -- Audio Devices --
    with gr.Accordion(i18n("Audio Devices"), open=True):
        with gr.Row():
            input_device = gr.Dropdown(
                label=i18n("Input Device (Microphone)"),
                info=i18n("Select your microphone."),
                choices=input_devs,
                value=default_input,
                interactive=True,
            )
            output_device = gr.Dropdown(
                label=i18n("Output Device (Speakers)"),
                info=i18n("Select your output device."),
                choices=output_devs,
                value=default_output,
                interactive=True,
            )

        refresh_devices = gr.Button(i18n("Refresh Devices"))

        with gr.Row():
            input_gain = gr.Slider(
                minimum=0, maximum=3,
                label=i18n("Input Gain"),
                value=1.0, step=0.1, interactive=True,
            )
            block_size = gr.Slider(
                minimum=512, maximum=8192,
                label=i18n("Block Size"),
                info=i18n("Larger = lower latency but more delay. Smaller = more responsive but heavier."),
                value=2048, step=128, interactive=True,
            )

    # -- Status & Controls --
    status = gr.JSON(
        value={"status": "Ready"} if HAS_SOUNDDEVICE else {"status": "Error: sounddevice not installed"},
    )

    with gr.Row():
        start_button = gr.Button(
            i18n("Start Realtime"),
            variant="primary",
            size="lg",
        )
        stop_button = gr.Button(
            i18n("Stop Realtime"),
            variant="stop",
            size="lg",
            interactive=False,
        )
        unload_button = gr.Button(
            i18n("Unload Model"),
            size="lg",
        )

    with gr.Row():
        refresh_models_btn = gr.Button(i18n("Refresh Models"))

    # -- Info --
    gr.Markdown(
        "### Notes\n"
        "- Uses your physical microphone and speakers (server mode).\n"
        "- No audio separation (UVR) is applied -- input goes directly to RVC.\n"
        "- Adjust block size based on your hardware: smaller blocks = more responsive but require faster GPU.\n"
        "- Requires `sounddevice` installed: `pip install sounddevice`.\n"
        "- Close other apps using your microphone to avoid conflicts."
    )

    # -- Event Handlers --

    def refresh_devices_fn():
        inputs, outputs = get_audio_devices()
        return (
            gr.update(choices=inputs, value=inputs[0] if inputs else None),
            gr.update(choices=outputs, value=outputs[0] if outputs else None),
        )

    def refresh_models_fn():
        models = get_model_files()
        indexes = get_index_files()
        return (
            gr.update(choices=models, value=models[0] if models else None),
            gr.update(choices=indexes, value=indexes[0] if indexes else None),
        )

    def update_rvc_params_fn(
        pitch_val, index_rate_val, protect_val, filter_radius_val,
        silence_thresh_val, f0_method_val, autotune_val,
    ):
        """Hot-swap RVC parameters while running."""
        global engine
        if engine and engine.is_running():
            engine.update_params(
                pitch=pitch_val,
                index_rate=index_rate_val,
                protect=protect_val,
                filter_radius=int(filter_radius_val),
                silence_threshold=silence_thresh_val,
                f0_method=f0_method_val,
                f0_autotune=autotune_val,
            )

    def unload_fn():
        global engine
        if engine:
            engine.cleanup()
            engine = None
        return {"status": "Model unloaded"}

    def status_updater():
        """Generator that continuously yields status updates."""
        global engine, running
        while running and engine:
            st = engine.get_status()
            if st["running"]:
                yield (
                    {"status": "Running", "latency": f"{st['latency_ms']:.1f} ms", "volume": f"{st['volume_db']:.1f} dB"},
                    gr.update(interactive=False),
                    gr.update(interactive=True),
                )
            else:
                yield {"status": "Stopped"}, gr.update(interactive=True), gr.update(interactive=False)
            time.sleep(0.2)
        yield {"status": "Stopped"}, gr.update(interactive=True), gr.update(interactive=False)

    def start_fn(model_path, index_path, pitch_val, index_rate_val, protect_val,
                 filter_radius_val, silence_thresh_val, f0_method_val,
                 autotune_val, embedder, in_dev, out_dev, block_sz):
        global engine, running, status_thread

        if not HAS_SOUNDDEVICE:
            return {"status": "Error: sounddevice not installed"}, gr.update(interactive=True), gr.update(interactive=False)

        if not model_path:
            return {"status": "Error: No model selected"}, gr.update(interactive=True), gr.update(interactive=False)

        try:
            from main.realtime import RealtimeVC

            # Cleanup previous engine
            if engine:
                engine.cleanup()

            engine = RealtimeVC(
                sample_rate=48000,
                silence_threshold=silence_thresh_val,
            )

            engine.load_model(
                model_path=model_path,
                index_path=index_path if index_path else "",
                sid=0,
                embedder_model=embedder,
            )

            engine.update_params(
                pitch=pitch_val,
                index_rate=index_rate_val,
                protect=protect_val,
                filter_radius=int(filter_radius_val),
                f0_method=f0_method_val,
                f0_autotune=autotune_val,
            )

            # Resolve device names to IDs
            in_id = None
            out_id = None
            devices = sd.query_devices()
            for i, dev in enumerate(devices):
                if dev["name"] == in_dev and dev["max_input_channels"] > 0:
                    in_id = i
                if dev["name"] == out_dev and dev["max_output_channels"] > 0:
                    out_id = i

            engine.start(
                input_device=in_id,
                output_device=out_id,
                block_size=int(block_sz),
            )

            running = True

            # Start status update thread
            status_thread = threading.Thread(
                target=lambda: list(status_updater()),
                daemon=True,
            )

            return (
                {"status": "Starting..."},
                gr.update(interactive=False),
                gr.update(interactive=True),
            )

        except Exception as e:
            return {"status": f"Error: {e}"}, gr.update(interactive=True), gr.update(interactive=False)

    def stop_fn():
        global engine, running
        running = False
        if engine:
            engine.stop()
        return {"status": "Stopped"}, gr.update(interactive=True), gr.update(interactive=False)

    # Connect handlers
    refresh_devices.click(
        fn=refresh_devices_fn,
        inputs=[],
        outputs=[input_device, output_device],
    )

    refresh_models_btn.click(
        fn=refresh_models_fn,
        inputs=[],
        outputs=[model_file, index_file],
    )

    unload_button.click(
        fn=unload_fn,
        inputs=[],
        outputs=[status],
    )

    # Hot-swap params on change
    for component in [pitch, index_rate, protect, filter_radius,
                      silence_threshold, pitch_extract, autotune]:
        component.change(
            fn=update_rvc_params_fn,
            inputs=[pitch, index_rate, protect, filter_radius,
                    silence_threshold, pitch_extract, autotune],
            outputs=[],
        )

    start_button.click(
        fn=start_fn,
        inputs=[
            model_file, index_file, pitch, index_rate, protect,
            filter_radius, silence_threshold, pitch_extract,
            autotune, embedder_model, input_device, output_device,
            block_size,
        ],
        outputs=[status, start_button, stop_button],
    )

    stop_button.click(
        fn=stop_fn,
        inputs=[],
        outputs=[status, start_button, stop_button],
    )
