"""
Whisper Transcription and Speaker Diarization Tab for Hyper-RVC.

Provides interface for:
- Speech-to-text transcription using Whisper
- Speaker diarization (identifying who spoke when)
- Word-level timestamps
- Multiple language support
"""

import os
import sys
import gradio as gr
import torch
import json
from typing import Dict, Any, List
from multiprocessing import Queue
import threading

now_dir = os.getcwd()
sys.path.append(now_dir)

from assets.i18n.i18n import I18nAuto
from main import whisper_process
from main.tools.variables import check_fp16_support
from main.tools.logger import get_logger

logger = get_logger(__name__)
i18n = I18nAuto()

# Supported audio formats
SUPPORTED_AUDIO_FORMATS = {
    "wav", "mp3", "flac", "ogg", "opus", "m4a", "aac", "wma", "aiff"
}

# Whisper model sizes
WHISPER_MODELS = {
    "tiny": "39M parameters, fastest, lower accuracy",
    "base": "74M parameters, fast, good accuracy",
    "small": "244M parameters, balanced speed/accuracy",
    "medium": "769M parameters, slower, high accuracy",
    "large": "1550M parameters, slowest, best accuracy",
    "large-v2": "1550M parameters, improved large model",
    "large-v3": "1550M parameters, latest large model",
}

# Available devices
def get_available_devices():
    """Get available computing devices."""
    devices = ["cpu"]
    if torch.cuda.is_available():
        devices.append("cuda")
    if torch.backends.mps.is_available():
        devices.append("mps")
    return devices


def format_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS.mmm format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    else:
        return f"{minutes:02d}:{secs:02d}.{millis:03d}"


def format_segments(segments: List[Dict]) -> str:
    """Format transcription segments into readable text."""
    if not segments:
        return "No transcription generated."

    formatted = []
    for seg in segments:
        start = format_timestamp(seg.get("start", 0))
        end = format_timestamp(seg.get("end", 0))
        text = seg.get("text", "").strip()
        speaker = seg.get("speaker", "")

        if speaker:
            formatted.append(f"[{start} -> {end}] {speaker}: {text}")
        else:
            formatted.append(f"[{start} -> {end}] {text}")

    return "\n".join(formatted)


def save_transcription(segments: List[Dict], output_path: str, output_format: str = "txt") -> str:
    """Save transcription to file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if output_format == "txt":
        with open(output_path, "w", encoding="utf-8") as f:
            for seg in segments:
                start = format_timestamp(seg.get("start", 0))
                end = format_timestamp(seg.get("end", 0))
                text = seg.get("text", "").strip()
                speaker = seg.get("speaker", "")

                if speaker:
                    f.write(f"[{start} -> {end}] {speaker}: {text}\n")
                else:
                    f.write(f"[{start} -> {end}] {text}\n")

    elif output_format == "json":
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(segments, f, indent=2, ensure_ascii=False)

    elif output_format == "srt":
        with open(output_path, "w", encoding="utf-8") as f:
            for i, seg in enumerate(segments, 1):
                start = format_timestamp_srt(seg.get("start", 0))
                end = format_timestamp_srt(seg.get("end", 0))
                text = seg.get("text", "").strip()

                f.write(f"{i}\n")
                f.write(f"{start} --> {end}\n")
                f.write(f"{text}\n\n")

    elif output_format == "vtt":
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("WEBVTT\n\n")
            for seg in segments:
                start = format_timestamp_vtt(seg.get("start", 0))
                end = format_timestamp_vtt(seg.get("end", 0))
                text = seg.get("text", "").strip()

                f.write(f"{start} --> {end}\n")
                f.write(f"{text}\n\n")

    return output_path


def format_timestamp_srt(seconds: float) -> str:
    """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_timestamp_vtt(seconds: float) -> str:
    """Convert seconds to VTT timestamp format (HH:MM:SS.mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def run_whisper_transcription(
    audio_path: str,
    model_size: str,
    device: str,
    language: str,
    word_timestamps: bool,
    output_format: str,
    output_dir: str
):
    """Run Whisper transcription on audio file."""
    if not os.path.exists(audio_path):
        return "Error: Audio file not found", "", ""

    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    output_path = os.path.join(output_dir, f"{base_name}_transcription.{output_format}")

    out_queue = Queue()
    configs = {}

    def run_in_thread():
        whisper_process(
            model_size=model_size,
            input_audio=audio_path,
            configs=configs,
            device=device,
            out_queue=out_queue,
            word_timestamps=word_timestamps
        )

    thread = threading.Thread(target=run_in_thread)
    thread.start()
    thread.join()

    try:
        result = out_queue.get(timeout=300)

        if isinstance(result, Exception):
            return f"Error: {str(result)}", "", ""

        segments = result
        save_transcription(segments, output_path, output_format)
        formatted_text = format_segments(segments)

        if segments and "language" in segments[0]:
            lang_info = f" (Detected: {segments[0]['language']})"
        else:
            lang_info = ""

        return f"Transcription completed successfully{lang_info}", formatted_text, output_path

    except Exception as e:
        return f"Error during transcription: {str(e)}", "", ""


def whisper_diarization_tab():
    """Create Whisper Transcription & Diarization tab."""

    default_output_dir = os.path.join(now_dir, "audio_files", "transcriptions")

    with gr.Tabs():
        with gr.TabItem(i18n("Transcription")):
            # Model Selection
            with gr.Row():
                with gr.Column(scale=2):
                    model_size = gr.Dropdown(
                        label=i18n("Model Size"),
                        info=i18n("Larger models are more accurate but slower"),
                        choices=list(WHISPER_MODELS.keys()),
                        value="large-v3",
                        interactive=True,
                    )
                    model_info = gr.Markdown(
                        value=WHISPER_MODELS["large-v3"],
                        label=i18n("Model Info")
                    )
                with gr.Column(scale=1):
                    device = gr.Radio(
                        label=i18n("Device"),
                        info=i18n("Select computing device"),
                        choices=get_available_devices(),
                        value="cuda" if torch.cuda.is_available() else "cpu",
                        interactive=True,
                    )

            # Audio Input
            upload_audio = gr.Audio(
                label=i18n("Upload Audio"),
                type="filepath",
                editable=False,
                sources="upload",
            )
            gr.Markdown(
                value=f"**Supported formats:** {', '.join(SUPPORTED_AUDIO_FORMATS)}",
                label=i18n("Supported Formats")
            )

            # Transcription Settings
            with gr.Accordion(i18n("Transcription Settings"), open=False):
                with gr.Row():
                    with gr.Column():
                        language = gr.Dropdown(
                            label=i18n("Language"),
                            info=i18n("Select language or leave empty for auto-detection"),
                            choices=[
                                ("Auto-detect", ""),
                                ("English", "en"),
                                ("Chinese", "zh"),
                                ("German", "de"),
                                ("Spanish", "es"),
                                ("Russian", "ru"),
                                ("Korean", "ko"),
                                ("French", "fr"),
                                ("Japanese", "ja"),
                                ("Portuguese", "pt"),
                                ("Turkish", "tr"),
                                ("Polish", "pl"),
                                ("Catalan", "ca"),
                                ("Dutch", "nl"),
                                ("Arabic", "ar"),
                                ("Swedish", "sv"),
                                ("Italian", "it"),
                                ("Indonesian", "id"),
                                ("Hindi", "hi"),
                                ("Finnish", "fi"),
                                ("Vietnamese", "vi"),
                                ("Hebrew", "he"),
                                ("Ukrainian", "uk"),
                                ("Greek", "el"),
                                ("Malay", "ms"),
                                ("Czech", "cs"),
                                ("Romanian", "ro"),
                                ("Danish", "da"),
                                ("Hungarian", "hu"),
                                ("Tamil", "ta"),
                                ("Norwegian", "no"),
                                ("Thai", "th"),
                                ("Urdu", "ur"),
                                ("Croatian", "hr"),
                                ("Bulgarian", "bg"),
                                ("Lithuanian", "lt"),
                                ("Latin", "la"),
                                ("Maori", "mi"),
                                ("Malayalam", "ml"),
                                ("Welsh", "cy"),
                                ("Slovak", "sk"),
                                ("Telugu", "te"),
                                ("Persian", "fa"),
                                ("Latvian", "lv"),
                                ("Bengali", "bn"),
                                ("Serbian", "sr"),
                                ("Azerbaijani", "az"),
                                ("Slovenian", "sl"),
                                ("Kannada", "kn"),
                                ("Estonian", "et"),
                                ("Macedonian", "mk"),
                                ("Breton", "br"),
                                ("Basque", "eu"),
                                ("Icelandic", "is"),
                                ("Armenian", "hy"),
                                ("Nepali", "ne"),
                                ("Mongolian", "mn"),
                                ("Bosnian", "bs"),
                                ("Kazakh", "kk"),
                                ("Albanian", "sq"),
                                ("Swahili", "sw"),
                                ("Galician", "gl"),
                                ("Marathi", "mr"),
                                ("Punjabi", "pa"),
                            ],
                            value="",
                            interactive=True,
                        )
                        word_timestamps = gr.Checkbox(
                            label=i18n("Word Timestamps"),
                            info=i18n("Extract word-level timestamps (slower)"),
                            value=True,
                            interactive=True,
                        )

                    with gr.Column():
                        output_format = gr.Radio(
                            label=i18n("Output Format"),
                            info=i18n("Select output file format"),
                            choices=[
                                ("Plain Text (TXT)", "txt"),
                                ("JSON", "json"),
                                ("Subtitles (SRT)", "srt"),
                                ("WebVTT (VTT)", "vtt"),
                            ],
                            value="txt",
                            interactive=True,
                        )
                        output_dir = gr.Textbox(
                            label=i18n("Output Directory"),
                            info=i18n("Directory to save transcription files"),
                            value=default_output_dir,
                            interactive=True,
                        )

            # Action Buttons
            with gr.Row():
                transcribe_button = gr.Button(
                    i18n("Transcribe Audio"),
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
                        info=i18n("Processing status and information"),
                        lines=2,
                        interactive=False,
                    )
                    output_file_path = gr.Textbox(
                        label=i18n("Output File Path"),
                        info=i18n("Path to saved transcription file"),
                        lines=1,
                        interactive=False,
                    )
                with gr.Column():
                    transcription_output = gr.Textbox(
                        label=i18n("Transcription"),
                        info=i18n("Transcribed text with timestamps"),
                        lines=15,
                        max_lines=50,
                    )

            # Info section
            with gr.Accordion(i18n("About Whisper Transcription"), open=False):
                gr.Markdown(
                    value="""
                    ### Whisper AI Speech Recognition

                    [Whisper](https://github.com/openai/whisper) is an automatic speech recognition (ASR) system trained by OpenAI.

                    **Features:**
                    - Multi-language support (99+ languages)
                    - Auto language detection
                    - Word-level timestamps
                    - Robust to noise and accents
                    - Translation to English

                    **Model Comparison:**
                    - **Tiny/Base**: Fast, good for quick tests
                    - **Small/Medium**: Balanced speed and accuracy
                    - **Large/Large-v3**: Best accuracy, recommended for production

                    **Tips:**
                    - Use larger models for better accuracy
                    - Enable word timestamps for precise segmentation
                    - Select known language for better results
                    """
                )

    # Event Handlers
    def update_model_info(model_choice):
        return WHISPER_MODELS.get(model_choice, "Unknown model")

    def clear_all():
        return (
            "",
            "",
            "",
            "Ready to transcribe"
        )

    # Connect event handlers
    model_size.change(
        fn=update_model_info,
        inputs=[model_size],
        outputs=[model_info]
    )

    clear_button.click(
        fn=clear_all,
        inputs=[],
        outputs=[status_output, output_file_path, transcription_output]
    )

    transcribe_button.click(
        fn=run_whisper_transcription,
        inputs=[
            upload_audio,
            model_size,
            device,
            language,
            word_timestamps,
            output_format,
            output_dir
        ],
        outputs=[status_output, transcription_output, output_file_path]
    )

    return transcription_output
