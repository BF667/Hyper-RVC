import gradio as gr
import shutil
import os
import sys
import re

from main.tools.downloader import download_model, DOWNLOAD_METHODS
from main.rvc.engine.lib.utils import format_title
from assets.i18n.i18n import I18nAuto

now_dir = os.getcwd()
sys.path.append(now_dir)

i18n = I18nAuto()

METHOD_DESCRIPTIONS = {
    "auto": "Auto-detect source from URL",
    "gdrive": "Google Drive",
    "huggingface": "HuggingFace",
    "mediafire": "MediaFire",
    "pixeldrain": "PixelDrain",
    "yandex": "Yandex Disk",
    "discord": "Discord CDN",
    "applio": "Applio.org Models",
    "direct": "Direct URL (any file)",
}


def _build_method_choices():
    """Return a list of display strings for the dropdown."""
    return [f"{m} ({METHOD_DESCRIPTIONS.get(m, '')})" for m in DOWNLOAD_METHODS]


def _parse_method(choice):
    """Extract method key from display string like 'auto (Auto-detect...)'."""
    return choice.split(" (")[0] if " (" in choice else choice


def _detect_method_for_url(url):
    """Auto-detect method and return the full display string."""
    from main.tools.downloader import detect_method
    detected = detect_method(url or "")
    return f"{detected} ({METHOD_DESCRIPTIONS.get(detected, '')})"


def save_drop_model(dropbox):
    if "pth" not in dropbox and "index" not in dropbox:
        raise gr.Error(
            message="The file you dropped is not a valid model file. Please try again."
        )
    else:
        file_name = format_title(os.path.basename(dropbox))
        if ".pth" in dropbox:
            model_name = format_title(file_name.split(".pth")[0])
        else:
            if (
                "v2" not in dropbox
                and "added_" not in dropbox
                and "_nprobe_1_" not in dropbox
            ):
                model_name = format_title(file_name.split(".index")[0])
            else:
                if "v2" not in dropbox:
                    if "_nprobe_1_" in file_name and "_v1" in file_name:
                        model_name = format_title(
                            file_name.split("_nprobe_1_")[1].split("_v1")[0]
                        )
                    elif "added_" in file_name and "_v1" in file_name:
                        model_name = format_title(
                            file_name.split("added_")[1].split("_v1")[0]
                        )
                else:
                    if "_nprobe_1_" in file_name and "_v2" in file_name:
                        model_name = format_title(
                            file_name.split("_nprobe_1_")[1].split("_v2")[0]
                        )
                    elif "added_" in file_name and "_v2" in file_name:
                        model_name = format_title(
                            file_name.split("added_")[1].split("_v2")[0]
                        )

        model_name = re.sub(r"\d+[se]", "", model_name)
        if "__" in model_name:
            model_name = model_name.replace("__", "")

        model_path = os.path.join(now_dir, "logs", model_name)
        if not os.path.exists(model_path):
            os.makedirs(model_path)
        if os.path.exists(os.path.join(model_path, file_name)):
            os.remove(os.path.join(model_path, file_name))
        shutil.copy(dropbox, os.path.join(model_path, file_name))
        print(f"{file_name} saved in {model_path}")
        gr.Info(f"{file_name} saved in {model_path}")
    return None


def download_model_tab():
    gr.Markdown(
        "### Download Voice Model\n"
        "Paste a model URL and select the download method. "
        "Set to 'auto' to automatically detect the source."
    )

    with gr.Row():
        link = gr.Textbox(
            label=i18n("Model URL"),
            info=i18n("Google Drive, HuggingFace, MediaFire, PixelDrain, Yandex, Discord, Applio, or direct link."),
            lines=1,
            scale=3,
        )
        method_dropdown = gr.Dropdown(
            label=i18n("Download Method"),
            info=i18n("Select source or use auto-detect."),
            choices=_build_method_choices(),
            value=_build_method_choices()[0],
            interactive=True,
            scale=2,
        )

    with gr.Row():
        download = gr.Button(i18n("Download"), variant="primary")
        auto_detect_btn = gr.Button(i18n("Auto-detect method"))

    output = gr.Textbox(
        label=i18n("Output Information"),
        info=i18n("Download progress and results will be displayed here."),
    )

    def on_auto_detect(url):
        if not url or not url.strip():
            return gr.update()
        return gr.update(value=_detect_method_for_url(url.strip()))

    def on_download(url, method_choice):
        if not url or not url.strip():
            return "Error: No URL provided"
        method = _parse_method(method_choice)
        return download_model(url.strip(), method)

    auto_detect_btn.click(
        fn=on_auto_detect,
        inputs=[link],
        outputs=[method_dropdown],
    )

    download.click(
        fn=on_download,
        inputs=[link, method_dropdown],
        outputs=[output],
    )

    gr.Markdown(value=i18n("## Drop files"))
    dropbox = gr.File(
        label=i18n(
            "Drag your .pth file and .index file into this space. Drag one and then the other."
        ),
        type="filepath",
    )
    dropbox.upload(
        fn=save_drop_model,
        inputs=[dropbox],
        outputs=[dropbox],
    )
