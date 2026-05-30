"""
Hyper-RVC WebUI – main entry point.

Replaces the original ``main.py``.  Launch this file to start the Gradio
web interface:

    python app.py
    python app.py --port 8080 --share
    python app.py --open
"""

import gradio as gr
import sys
import os

now_dir = os.getcwd()
sys.path.append(now_dir)

DEFAULT_PORT = 7755
MAX_PORT_ATTEMPTS = 10

from assets.i18n.i18n import I18nAuto

i18n = I18nAuto()

import assets.themes.loadThemes as loadThemes

from tabs.full_inference import full_inference_tab
from tabs.download_model import download_model_tab
from tabs.download_music import download_music_tab
from tabs.settings import select_themes_tab
from tabs.whisper_transcription import whisper_diarization_tab
from tabs.tts_inference import tts_inference_tab
from tabs.realtime_tab import realtime_tab
from tabs.acestep_tab import acestep_tab

rvc_theme = loadThemes.load_json() or "ParityError/Interstellar"

with gr.Blocks(
    theme=rvc_theme, title="HyperRVC", css="footer{display:none !important}"
) as app:
    gr.Markdown("# HyperRVC WebUI")
    with gr.Tab(i18n("Inference")):
        with gr.Tab(i18n("Full Inference")):
            full_inference_tab()
        with gr.Tab(i18n("Realtime")):
            realtime_tab()
        with gr.Tab(i18n("TTS")):
            tts_inference_tab()
        with gr.Tab(i18n("Whisper")):
            whisper_diarization_tab()
    with gr.Tab(i18n("Download")):
        with gr.Tab(i18n("Download Model")):
            download_model_tab()
        with gr.Tab(i18n("Download Music")):
            download_music_tab()
    with gr.Tab(i18n("ACE-Step")):
        acestep_tab()
    with gr.Tab(i18n("Settings")):
        select_themes_tab()


def launch(port):
    app.launch(
        favicon_path=os.path.join(now_dir, "assets", "logo.ico"),
        share="--share" in sys.argv,
        inbrowser="--open" in sys.argv,
        server_port=port,
    )


def get_port_from_args():
    if "--port" in sys.argv:
        port_index = sys.argv.index("--port") + 1
        if port_index < len(sys.argv):
            return int(sys.argv[port_index])
    return DEFAULT_PORT


if __name__ == "__main__":
    port = get_port_from_args()
    for _ in range(MAX_PORT_ATTEMPTS):
        try:
            launch(port)
            break
        except OSError:
            print(
                f"Failed to launch on port {port}, trying again on port {port - 1}..."
            )
            port -= 1
        except Exception as error:
            print(f"An error occurred launching Gradio: {error}")
            break
