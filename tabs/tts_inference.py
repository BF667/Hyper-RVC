"""
TTS (Text-to-Speech) Inference Tab for Hyper-RVC.

Provides interface for:
- Text-to-Speech using Edge TTS (Microsoft Azure voices)
- Voice Conversion using RVC models
- Combined TTS + VC pipeline
- Multiple voice and language options
"""

import os
import sys
import gradio as gr
import torch
from typing import Optional

now_dir = os.getcwd()
sys.path.append(now_dir)

from assets.i18n.i18n import I18nAuto
from main import (
    run_tts_inference,
    get_tts_voices,
    get_tts_languages,
    get_tts_rate_options,
    EDGE_TTS_VOICES,
    TTS_RATE_OPTIONS,
)
from main.tools.logger import get_logger
from main.tools.variables import get_f0_methods_ui

logger = get_logger(__name__)
i18n = I18nAuto()


def get_model_indexes():
    """Get list of available RVC models and indexes."""
    model_root = os.path.join(now_dir, "logs")
    model_root_relative = os.path.relpath(model_root, now_dir)

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

    return sorted(names), sorted(indexes_list)


def tts_inference_tab():
    """Create TTS Inference tab."""

    # Get available models
    models, indexes = get_model_indexes()
    default_model = models[0] if models else ""
    default_index = indexes[0] if indexes else ""

    # Get device
    default_device = "0" if torch.cuda.is_available() else "-"

    with gr.Tabs():
        with gr.TabItem(i18n("TTS Generation")):
            # Text Input
            text_input = gr.Textbox(
                label=i18n("Text to Synthesize"),
                info=i18n("Enter the text you want to convert to speech (max 5000 characters)"),
                placeholder="Enter your text here...",
                lines=5,
                max_lines=20,
            )
            char_count = gr.Markdown(
                value="**0** / 5000 characters",
                label=i18n("Character Count")
            )

            # Voice Selection
            with gr.Row():
                with gr.Column(scale=2):
                    language = gr.Dropdown(
                        label=i18n("Language"),
                        info=i18n("Select the language for TTS"),
                        choices=list(EDGE_TTS_VOICES.keys()),
                        value="English (US)",
                        interactive=True,
                    )
                with gr.Column(scale=2):
                    voice = gr.Dropdown(
                        label=i18n("Voice"),
                        info=i18n("Select the voice to use"),
                        choices=EDGE_TTS_VOICES["English (US)"],
                        value="en-US-JennyNeural",
                        interactive=True,
                    )
                with gr.Column(scale=1):
                    rate = gr.Dropdown(
                        label=i18n("Speech Rate"),
                        info=i18n("Adjust speech speed"),
                        choices=list(TTS_RATE_OPTIONS.keys()),
                        value="Normal (0%)",
                        interactive=True,
                    )

            # RVC Voice Conversion Settings
            with gr.Accordion(i18n("RVC Voice Conversion (Optional)"), open=False):
                use_rvc = gr.Checkbox(
                    label=i18n("Enable RVC Voice Conversion"),
                    info=i18n("Convert TTS voice using RVC model"),
                    value=False,
                    interactive=True,
                )

                with gr.Column(visible=False) as rvc_settings:
                    with gr.Row():
                        with gr.Column():
                            model_file = gr.Dropdown(
                                label=i18n("Voice Model"),
                                info=i18n("Select RVC voice model"),
                                choices=models,
                                value=default_model,
                                interactive=True,
                                allow_custom_value=True,
                            )
                            index_file = gr.Dropdown(
                                label=i18n("Index File"),
                                info=i18n("Select index file"),
                                choices=indexes,
                                value=default_index,
                                interactive=True,
                                allow_custom_value=True,
                            )

                        with gr.Column():
                            refresh_models = gr.Button(
                                i18n("Refresh Models"),
                                size="sm"
                            )

                            pitch = gr.Slider(
                                label=i18n("Pitch"),
                                info=i18n("Adjust pitch in semitones"),
                                minimum=-12,
                                maximum=12,
                                step=1,
                                value=0,
                                interactive=True,
                            )

                    with gr.Row():
                        with gr.Column():
                            pitch_extract = gr.Radio(
                                label=i18n("Pitch Extractor"),
                                choices=get_f0_methods_ui(),
                                value="rmvpe",
                                interactive=True,
                            )
                            filter_radius = gr.Slider(
                                label=i18n("Filter Radius"),
                                minimum=0,
                                maximum=7,
                                step=1,
                                value=3,
                                interactive=True,
                            )

                        with gr.Column():
                            index_rate = gr.Slider(
                                label=i18n("Search Feature Ratio"),
                                minimum=0,
                                maximum=1,
                                step=0.05,
                                value=0.75,
                                interactive=True,
                            )
                            rms_mix_rate = gr.Slider(
                                label=i18n("Volume Envelope"),
                                minimum=0,
                                maximum=1,
                                step=0.05,
                                value=0.25,
                                interactive=True,
                            )

                        with gr.Column():
                            protect = gr.Slider(
                                label=i18n("Protect Voiceless Consonants"),
                                minimum=0,
                                maximum=0.5,
                                step=0.05,
                                value=0.33,
                                interactive=True,
                            )
                            embedder_model = gr.Radio(
                                label=i18n("Embedder Model"),
                                choices=["contentvec", "chinese-hubert-base"],
                                value="contentvec",
                                interactive=True,
                            )

            # Export Settings
            with gr.Accordion(i18n("Export Settings"), open=False):
                with gr.Row():
                    export_format = gr.Radio(
                        label=i18n("Export Format"),
                        choices=["WAV", "MP3", "FLAC", "OGG", "M4A"],
                        value="WAV",
                        interactive=True,
                    )
                    devices = gr.Textbox(
                        label=i18n("Device"),
                        info=i18n("GPU device IDs (use '-' for CPU)"),
                        value=default_device,
                        interactive=True,
                    )

            # Action Buttons
            with gr.Row():
                generate_button = gr.Button(
                    i18n("Generate TTS"),
                    variant="primary",
                    size="lg"
                )
                clear_button = gr.Button(
                    i18n("Clear"),
                    variant="stop",
                    size="lg"
                )

            # Output
            with gr.Row():
                with gr.Column():
                    status_output = gr.Textbox(
                        label=i18n("Status"),
                        info=i18n("Processing status"),
                        lines=2,
                        interactive=False,
                    )
                    tts_audio_output = gr.Audio(
                        label=i18n("TTS Audio (Before RVC)"),
                        type="filepath",
                        interactive=False,
                    )
                    rvc_audio_output = gr.Audio(
                        label=i18n("Final Audio (After RVC)"),
                        type="filepath",
                        interactive=False,
                        visible=False,
                    )
                with gr.Column():
                    output_info = gr.Markdown(
                        value="### Output Information\n\nAudio files will appear here after generation.",
                        label=i18n("Information")
                    )

            # Info section
            with gr.Accordion(i18n("About TTS"), open=False):
                gr.Markdown(
                    value="""
                    ### Edge TTS (Microsoft Azure)

                    **Edge TTS** provides high-quality neural text-to-speech using Microsoft Azure voices.

                    **Features:**
                    - 400+ natural-sounding voices
                    - 100+ languages and dialects
                    - Neural voice technology
                    - Free to use
                    - No API key required

                    **RVC Voice Conversion:**
                    - Convert TTS voice to any RVC model
                    - Combine Azure quality with custom voices
                    - Adjust pitch, timbre, and characteristics

                    **Tips:**
                    - Use punctuation for better prosody
                    - Break long texts into paragraphs
                    - Adjust rate for natural timing
                    - Use RVC for character voices
                    """
                )

    # Event Handlers
    def update_voice_list(language_choice):
        """Update voice list based on selected language."""
        voices = EDGE_TTS_VOICES.get(language_choice, EDGE_TTS_VOICES["English (US)"])
        return gr.update(choices=voices, value=voices[0] if voices else "")

    def toggle_rvc_settings(checked):
        """Show/hide RVC settings."""
        return gr.update(visible=checked)

    def update_char_count(text):
        """Update character count display."""
        return f"**{len(text)}** / 5000 characters"

    def refresh_model_list():
        """Refresh model and index lists."""
        models, indexes = get_model_indexes()
        return (
            gr.update(choices=models, value=models[0] if models else ""),
            gr.update(choices=indexes, value=indexes[0] if indexes else ""),
        )

    def clear_all():
        """Clear all outputs."""
        return (
            "",
            "Ready to generate",
            None,
            None,
            gr.update(visible=False),
        )

    def generate_tts(
        text,
        language,
        voice,
        rate_choice,
        use_rvc,
        model_path,
        index_path,
        pitch,
        pitch_extract,
        filter_radius,
        index_rate,
        rms_mix_rate,
        protect,
        embedder_model,
        devices,
        export_format,
    ):
        """Generate TTS and optionally apply RVC."""
        rate_value = TTS_RATE_OPTIONS.get(rate_choice, 0)

        status, tts_path, rvc_path = run_tts_inference(
            text=text,
            language=language,
            voice=voice,
            rate=rate_value,
            use_rvc=use_rvc,
            model_path=model_path,
            index_path=index_path,
            pitch=pitch,
            pitch_extract=pitch_extract,
            filter_radius=filter_radius,
            index_rate=index_rate,
            rms_mix_rate=rms_mix_rate,
            protect=protect,
            embedder_model=embedder_model,
            devices=devices,
            export_format=export_format,
        )

        # Determine visibility of RVC output
        rvc_visible = rvc_path is not None

        return (
            status,
            tts_path,
            rvc_path,
            gr.update(visible=rvc_visible),
        )

    # Connect event handlers
    language.change(
        fn=update_voice_list,
        inputs=[language],
        outputs=[voice]
    )

    use_rvc.change(
        fn=toggle_rvc_settings,
        inputs=[use_rvc],
        outputs=[rvc_settings]
    )

    text_input.change(
        fn=update_char_count,
        inputs=[text_input],
        outputs=[char_count]
    )

    refresh_models.click(
        fn=refresh_model_list,
        inputs=[],
        outputs=[model_file, index_file]
    )

    clear_button.click(
        fn=clear_all,
        inputs=[],
        outputs=[text_input, status_output, tts_audio_output, rvc_audio_output]
    )

    generate_button.click(
        fn=generate_tts,
        inputs=[
            text_input,
            language,
            voice,
            rate,
            use_rvc,
            model_file,
            index_file,
            pitch,
            pitch_extract,
            filter_radius,
            index_rate,
            rms_mix_rate,
            protect,
            embedder_model,
            devices,
            export_format,
        ],
        outputs=[status_output, tts_audio_output, rvc_audio_output]
    )

    return tts_audio_output
