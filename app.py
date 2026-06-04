"""
Hyper-RVC WebUI – main entry point using gradio.Server.

Architecture (following https://huggingface.co/blog/introducing-gradio-server):
  - gradio.Server extends FastAPI – full custom route support
  - @app.api() registers backend endpoints with Gradio's queuing engine
  - @app.get("/") serves the custom static HTML/CSS/JS front-end
  - The front-end connects via the Gradio JS Client (queuing, concurrency, etc.)
  - No Gradio UI components (gr.Blocks, gr.Tab, etc.) are used for the main UI
"""

import os
import sys
import json
import copy
import shutil
import datetime
import unicodedata

now_dir = os.getcwd()
sys.path.append(now_dir)

DEFAULT_PORT = 7755
MAX_PORT_ATTEMPTS = 10

# ─── Heavy imports ──────────────────────────────────────────────────────────
import torch
import regex as re

from gradio import Server
from gradio.data_classes import FileData
from fastapi.responses import HTMLResponse
from fastapi import UploadFile, File as FastAPIFile

from assets.i18n.i18n import I18nAuto
import assets.themes.theme_editor as te
from main.core import full_inference_program
from main.rvc.converter import run_rvc_conversion
from main.tools.variables import get_f0_methods_ui
from main.tools.downloader import download_model as dl_model, DOWNLOAD_METHODS, detect_method
from main.rvc.engine.lib.utils import format_title as fmt_title
from main.tools.logger import get_logger
from main import download_music, run_tts_inference, get_tts_voices, get_tts_languages, get_tts_rate_options, EDGE_TTS_VOICES, TTS_RATE_OPTIONS
from main.whisper.transcriber import whisper_process
from main.tools.variables import check_fp16_support

logger = get_logger(__name__)
i18n = I18nAuto()

# ─── Path configuration ─────────────────────────────────────────────────────
model_root = os.path.join(now_dir, "logs")
audio_root = os.path.join(now_dir, "audio_files", "original_files")
PRESETS_DIR = os.path.join(now_dir, "assets", "presets")
CONFIG_PATH = os.path.join(now_dir, "assets", "config.json")
STATIC_DIR = os.path.join(now_dir, "assets", "static")

os.makedirs(PRESETS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

sup_audioext = {
    "wav", "mp3", "flac", "ogg", "opus", "m4a", "mp4",
    "aac", "alac", "wma", "aiff", "webm", "ac3",
}

# ─── Audio separation model lists ───────────────────────────────────────────
vocals_model_names = ["Mel-Roformer by KimberleyJSN", "BS-Roformer by ViperX", "MDX23C"]
karaoke_models_names = ["Mel-Roformer Karaoke by aufr33 and viperx", "UVR-BVE"]
dereverb_models_names = [
    "MDX23C DeReverb by aufr33 and jarredou",
    "UVR-Deecho-Dereverb",
    "MDX Reverb HQ by FoxJoy",
    "BS-Roformer Dereverb by anvuew",
]
deecho_models_names = ["UVR-Deecho-Normal", "UVR-Deecho-Aggressive"]
denoise_models_names = [
    "Mel-Roformer Denoise Normal by aufr33",
    "Mel-Roformer Denoise Aggressive by aufr33",
    "UVR Denoise",
]

whisper_model_sizes = ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]


# ─── File discovery helpers ─────────────────────────────────────────────────
def _get_models():
    return sorted([
        os.path.join(root, file)
        for root, _, files in os.walk(model_root, topdown=False)
        for file in files
        if file.endswith((".pth", ".onnx")) and not (file.startswith("G_") or file.startswith("D_"))
    ])


def _get_indexes():
    return sorted([
        os.path.join(dirpath, filename)
        for dirpath, _, filenames in os.walk(model_root)
        for filename in filenames
        if filename.endswith(".index") and "trained" not in filename
    ])


def _get_audio_files():
    return sorted([
        os.path.join(root, name)
        for root, _, files in os.walk(audio_root, topdown=False)
        for name in files
        if name.endswith(tuple(sup_audioext)) and root == audio_root and "_output" not in name
    ])


def _match_index(model_path):
    if not model_path:
        return ""
    model_folder = os.path.dirname(model_path)
    model_name = os.path.basename(model_path)
    base_name = os.path.splitext(model_name)[0]
    for idx in _get_indexes():
        if os.path.dirname(idx) == model_folder:
            idx_base = os.path.splitext(os.path.basename(idx))[0]
            if idx_base == base_name:
                return idx
    for idx in _get_indexes():
        if os.path.dirname(idx) == model_folder:
            return idx
    for idx in _get_indexes():
        if model_name in os.path.basename(idx):
            return idx
    return ""


def _get_speakers_id(model_path):
    if model_path:
        try:
            model_data = torch.load(os.path.join(now_dir, model_path), map_location="cpu", weights_only=True)
            speakers_id = model_data.get("speakers_id")
            if speakers_id:
                return list(range(speakers_id))
        except Exception:
            pass
    return [0]


def _format_title(title):
    formatted = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("utf-8")
    formatted = re.sub(r"[\u2500-\u257F]+", "", formatted)
    formatted = re.sub(r"[^\w\s.-]", "", formatted)
    formatted = re.sub(r"\s+", "_", formatted)
    return formatted


def _get_number_of_gpus():
    if torch.cuda.is_available():
        return "-".join(map(str, range(torch.cuda.device_count())))
    return "-"


# ═══════════════════════════════════════════════════════════════════════════
# Create the gradio.Server app
# ═══════════════════════════════════════════════════════════════════════════
app = Server()


# ─── Serve the custom static front-end ──────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def homepage():
    html_path = os.path.join(STATIC_DIR, "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


# ─── Data / list endpoints ──────────────────────────────────────────────────
@app.api(name="get_models")
def api_get_models():
    return _get_models()


@app.api(name="get_indexes")
def api_get_indexes():
    return _get_indexes()


@app.api(name="get_audio_files")
def api_get_audio_files():
    return _get_audio_files()


@app.api(name="match_index")
def api_match_index(model_path: str):
    return _match_index(model_path)


@app.api(name="get_speakers_id")
def api_get_speakers_id(model_path: str):
    return _get_speakers_id(model_path)


@app.api(name="get_separation_models")
def api_get_separation_models():
    return {
        "vocals": vocals_model_names,
        "karaoke": karaoke_models_names,
        "dereverb": dereverb_models_names,
        "deecho": deecho_models_names,
        "denoise": denoise_models_names,
    }


@app.api(name="get_f0_methods")
def api_get_f0_methods():
    return get_f0_methods_ui()


@app.api(name="get_gpus")
def api_get_gpus():
    return _get_number_of_gpus()


@app.api(name="get_embedder_models")
def api_get_embedder_models():
    return ["contentvec", "chinese-hubert-base", "japanese-hubert-base", "korean-hubert-base"]


@app.api(name="get_download_methods")
def api_get_download_methods():
    descriptions = {
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
    return {m: descriptions.get(m, "") for m in DOWNLOAD_METHODS}


@app.api(name="detect_download_method")
def api_detect_download_method(url: str):
    return detect_method(url or "")


@app.api(name="get_tts_voices_data")
def api_get_tts_voices_data():
    return {"voices": EDGE_TTS_VOICES, "rate_options": TTS_RATE_OPTIONS}


@app.api(name="get_whisper_models")
def api_get_whisper_models():
    descriptions = {
        "tiny": "39M parameters, fastest, lower accuracy",
        "base": "74M parameters, fast, good accuracy",
        "small": "244M parameters, balanced speed/accuracy",
        "medium": "769M parameters, slower, high accuracy",
        "large": "1550M parameters, slowest, best accuracy",
        "large-v2": "1550M parameters, improved large model",
        "large-v3": "1550M parameters, latest large model",
    }
    return descriptions


@app.api(name="get_available_devices")
def api_get_available_devices():
    devices = ["cpu"]
    if torch.cuda.is_available():
        devices.append("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        devices.append("mps")
    return devices


# ─── Inference endpoints ────────────────────────────────────────────────────
@app.api(name="full_inference")
def api_full_inference(params: dict):
    try:
        message, output_file = full_inference_program(**params)
        return {"status": message, "output_file": output_file}
    except Exception as e:
        return {"status": f"Error: {str(e)}", "output_file": None}


@app.api(name="batch_convert")
def api_batch_convert(params: dict):
    try:
        input_folder = params.get("input_folder", "")
        output_folder = params.get("output_folder", "")
        model_path = params.get("model_path", "")
        index_path = params.get("index_path", "")

        if not model_path or not input_folder or not output_folder:
            return "Please fill in all required fields."

        os.makedirs(output_folder, exist_ok=True)
        processed, errors = 0, 0
        lines = []

        for name in sorted(os.listdir(input_folder)):
            if not name.endswith(tuple(sup_audioext)) or "_output" in name:
                continue
            input_path = os.path.join(input_folder, name)
            base = os.path.splitext(name)[0]
            ext = (params.get("export_format", "wav") or "wav").lower()
            output_path = os.path.join(output_folder, f"{base}_output.{ext}")
            try:
                run_rvc_conversion(
                    audio_input_path=input_path,
                    audio_output_path=output_path,
                    model_path=model_path,
                    index_path=index_path,
                    embedder_model=params.get("embedder_model", "contentvec"),
                    pitch=params.get("pitch", 0),
                    f0_method=params.get("pitch_extract", "rmvpe"),
                    filter_radius=params.get("filter_radius", 3),
                    index_rate=params.get("index_rate", 0.75),
                    volume_envelope=params.get("rms_mix_rate", 0.25),
                    protect=params.get("protect", 0.33),
                    split_audio=params.get("split_audio", False),
                    f0_autotune=params.get("autotune", False),
                    hop_length=params.get("hop_length", 64),
                    export_format=params.get("export_format", "wav"),
                )
                processed += 1
                lines.append(f"  OK: {name} -> {base}_output.{ext}")
            except Exception as exc:
                errors += 1
                lines.append(f"  FAIL: {name} — {str(exc)[:100]}")

        return f"Processed: {processed} | Errors: {errors}\n" + "\n".join(lines)
    except Exception as e:
        return f"Error: {str(e)}"


# ─── Download endpoints ─────────────────────────────────────────────────────
@app.api(name="download_model")
def api_download_model(url: str, method: str):
    try:
        return dl_model(url.strip(), method)
    except Exception as e:
        return f"Error: {str(e)}"


@app.api(name="download_music")
def api_download_music(url: str):
    try:
        return download_music(url.strip())
    except Exception as e:
        return f"Error: {str(e)}"


@app.api(name="upload_model_file")
def api_upload_model_file(file_data: FileData):
    try:
        dropbox = file_data["path"]
        if "pth" not in dropbox and "index" not in dropbox:
            return "Error: Not a valid model file (.pth or .index)"
        file_name = fmt_title(os.path.basename(dropbox))
        if ".pth" in dropbox:
            model_name = fmt_title(file_name.split(".pth")[0])
        else:
            model_name = fmt_title(file_name.split(".index")[0])

        model_name = re.sub(r"\d+[se]", "", model_name)
        if "__" in model_name:
            model_name = model_name.replace("__", "")

        model_path = os.path.join(now_dir, "logs", model_name)
        os.makedirs(model_path, exist_ok=True)
        target = os.path.join(model_path, file_name)
        if os.path.exists(target):
            os.remove(target)
        shutil.copy(dropbox, target)
        return f"{file_name} saved in {model_path}"
    except Exception as e:
        return f"Error: {str(e)}"


# ─── TTS endpoint ───────────────────────────────────────────────────────────
@app.api(name="tts_generate")
def api_tts_generate(params: dict):
    try:
        rate_value = TTS_RATE_OPTIONS.get(params.get("rate", "Normal (0%)"), 0)
        status, tts_path, rvc_path = run_tts_inference(
            text=params.get("text", ""),
            language=params.get("language", "English (US)"),
            voice=params.get("voice", "en-US-JennyNeural"),
            rate=rate_value,
            use_rvc=params.get("use_rvc", False),
            model_path=params.get("model_path", ""),
            index_path=params.get("index_path", ""),
            pitch=params.get("pitch", 0),
            pitch_extract=params.get("pitch_extract", "rmvpe"),
            filter_radius=params.get("filter_radius", 3),
            index_rate=params.get("index_rate", 0.75),
            rms_mix_rate=params.get("rms_mix_rate", 0.25),
            protect=params.get("protect", 0.33),
            embedder_model=params.get("embedder_model", "contentvec"),
            devices=params.get("devices", "0"),
            export_format=params.get("export_format", "WAV"),
        )
        return {"status": status, "tts_audio": tts_path, "rvc_audio": rvc_path}
    except Exception as e:
        return {"status": f"Error: {str(e)}", "tts_audio": None, "rvc_audio": None}


# ─── Whisper endpoint ───────────────────────────────────────────────────────
@app.api(name="whisper_transcribe")
def api_whisper_transcribe(params: dict):
    try:
        from multiprocessing import Queue
        import threading

        audio_path = params.get("audio_path", "")
        if not os.path.exists(audio_path):
            return {"status": "Error: Audio file not found", "transcription": "", "output_path": ""}

        model_size = params.get("model_size", "large-v3")
        device = params.get("device", "cuda" if torch.cuda.is_available() else "cpu")
        language = params.get("language", "")
        word_timestamps = params.get("word_timestamps", True)
        output_format = params.get("output_format", "txt")
        output_dir = params.get("output_dir", os.path.join(now_dir, "audio_files", "transcriptions"))

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
                word_timestamps=word_timestamps,
            )

        thread = threading.Thread(target=run_in_thread)
        thread.start()
        thread.join()

        result = out_queue.get(timeout=300)
        if isinstance(result, Exception):
            return {"status": f"Error: {str(result)}", "transcription": "", "output_path": ""}

        segments = result

        # Format transcription
        formatted = []
        for seg in segments:
            start = seg.get("start", 0)
            end = seg.get("end", 0)
            text = seg.get("text", "").strip()
            speaker = seg.get("speaker", "")
            sh, sm, ss = int(start // 3600), int((start % 3600) // 60), int(start % 60)
            eh, em, es = int(end // 3600), int((end % 3600) // 60), int(end % 60)
            start_str = f"{sh:02d}:{sm:02d}:{ss:02d}" if sh > 0 else f"{sm:02d}:{ss:02d}"
            end_str = f"{eh:02d}:{em:02d}:{es:02d}" if eh > 0 else f"{em:02d}:{es:02d}"
            if speaker:
                formatted.append(f"[{start_str} -> {end_str}] {speaker}: {text}")
            else:
                formatted.append(f"[{start_str} -> {end_str}] {text}")

        lang_info = ""
        if segments and "language" in segments[0]:
            lang_info = f" (Detected: {segments[0]['language']})"

        return {
            "status": f"Transcription completed{lang_info}",
            "transcription": "\n".join(formatted),
            "output_path": output_path,
        }
    except Exception as e:
        return {"status": f"Error: {str(e)}", "transcription": "", "output_path": ""}


# ─── ACE-Step endpoints ─────────────────────────────────────────────────────
@app.api(name="acestep_load_models")
def api_acestep_load_models(params: dict):
    try:
        from main.acestep_inference import initialize_handlers
        return initialize_handlers(
            dit_model=params.get("dit_model", ""),
            lm_model=params.get("lm_model", ""),
            lm_backend=params.get("lm_backend", "pytorch"),
            device=params.get("device", "auto"),
            use_lm=params.get("use_lm", True),
        )
    except Exception as e:
        return f"Error: {str(e)}"


@app.api(name="acestep_unload_models")
def api_acestep_unload_models():
    try:
        from main.acestep_inference import unload_handlers
        return unload_handlers()
    except Exception as e:
        return f"Error: {str(e)}"


@app.api(name="acestep_generate")
def api_acestep_generate(params: dict):
    try:
        from main.acestep_inference import is_initialized, run_acestep_simple_mode, run_acestep_inference
        from main.tools.variables import ACESTEP_TIME_SIGNATURE_MAP as TIME_SIGNATURE_MAP

        if not is_initialized():
            return {"status": "Error: Models not loaded. Go to Model Setup first.", "audio": None}

        mode = params.get("mode", "Simple")
        if mode == "Simple":
            status, audio = run_acestep_simple_mode(
                query=params.get("query", ""),
                vocal_language=params.get("vocal_language", "en"),
                duration=params.get("duration", 30),
                inference_steps=params.get("inference_steps", 8),
                seed=int(params.get("seed", -1)),
                batch_size=int(params.get("batch_size", 1)),
                audio_format=params.get("audio_format", "wav"),
            )
        else:
            task_map = {"Custom": "text2music", "Cover": "cover", "Repaint": "repaint"}
            task = task_map.get(mode, "text2music")
            status, audio = run_acestep_inference(
                task_type=task,
                caption=params.get("caption", ""),
                lyrics=params.get("lyrics", ""),
                instrumental=params.get("instrumental", False),
                bpm=int(params.get("bpm", 0)) if params.get("bpm") else None,
                keyscale=params.get("keyscale", ""),
                timesignature=TIME_SIGNATURE_MAP.get(params.get("time_signature", "Auto"), ""),
                vocal_language=params.get("vocal_language", "en"),
                duration=params.get("duration", 30),
                src_audio=params.get("src_audio"),
                audio_cover_strength=params.get("cover_strength", 0.8),
                repainting_start=params.get("repaint_start", 0),
                repainting_end=params.get("repaint_end", -1),
                inference_steps=params.get("inference_steps", 8),
                guidance_scale=params.get("guidance_scale", 3.0),
                seed=int(params.get("seed", -1)),
                batch_size=int(params.get("batch_size", 1)),
                thinking=params.get("thinking", True),
                lm_temperature=params.get("lm_temperature", 0.8),
                audio_format=params.get("audio_format", "wav"),
            )
        return {"status": status, "audio": audio}
    except Exception as e:
        return {"status": f"Error: {str(e)}", "audio": None}


@app.api(name="acestep_get_defaults")
def api_acestep_get_defaults():
    try:
        from main.tools.variables import get_acestep_defaults
        return get_acestep_defaults()
    except Exception:
        return {}


# ─── Theme editor endpoints ─────────────────────────────────────────────────
@app.api(name="get_theme")
def api_get_theme():
    return te.get_active_theme()


@app.api(name="save_theme")
def api_save_theme(theme: dict):
    name = theme.get("name", "Untitled")
    return te.save_theme(theme, name)


@app.api(name="load_theme")
def api_load_theme(name: str):
    return te.load_theme(name)


@app.api(name="list_themes")
def api_list_themes():
    return te.list_saved_themes()


@app.api(name="delete_theme")
def api_delete_theme(name: str):
    return te.delete_theme(name)


@app.api(name="apply_theme")
def api_apply_theme(theme: dict):
    return te.set_active_theme(theme)


@app.api(name="get_theme_presets")
def api_get_theme_presets():
    return list(te.BUTTON_PRESETS.keys())


@app.api(name="apply_button_preset")
def api_apply_button_preset(preset_name: str):
    merged = te.apply_button_preset(te.get_active_theme(), preset_name)
    return merged


@app.api(name="reset_theme")
def api_reset_theme():
    return copy.deepcopy(te.DEFAULT_THEME)


@app.api(name="get_theme_css")
def api_get_theme_css():
    return te.generate_css()


# ─── Language / config endpoints ────────────────────────────────────────────
@app.api(name="get_languages")
def api_get_languages():
    from tabs.settings import get_available_languages
    return get_available_languages()


@app.api(name="save_language")
def api_save_language(language: str):
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        config.setdefault("lang", {})
        config["lang"]["selected_lang"] = language
        config["lang"]["override"] = True
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return "Language changed. Restart the app to apply."
    except Exception as e:
        return f"Error: {e}"


@app.api(name="get_config")
def api_get_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


@app.api(name="reset_config")
def api_reset_config():
    try:
        config = {
            "theme": {"file": None, "class": "HyperRVC"},
            "custom_theme": {},
            "lang": {"override": False, "selected_lang": "en_US"},
        }
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return "Settings reset. Restart the app to apply."
    except Exception as e:
        return f"Error: {e}"


# ─── Audio upload endpoint ──────────────────────────────────────────────────
@app.api(name="upload_audio")
def api_upload_audio(file_data: FileData):
    try:
        file_path = file_data["path"]
        safe_name = _format_title(os.path.basename(file_path))
        target_path = os.path.join(audio_root, safe_name)
        if os.path.exists(target_path):
            os.remove(target_path)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        shutil.copy(file_path, target_path)
        return target_path
    except Exception as e:
        return f"Error: {str(e)}"


# ─── Preset endpoints ──────────────────────────────────────────────────────
@app.api(name="list_presets")
def api_list_presets():
    if not os.path.isdir(PRESETS_DIR):
        return []
    return [f.rsplit(".", 1)[0] for f in os.listdir(PRESETS_DIR) if f.endswith(".json")]


@app.api(name="load_preset")
def api_load_preset(name: str):
    try:
        with open(os.path.join(PRESETS_DIR, f"{name}.json"), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


@app.api(name="save_preset")
def api_save_preset(params: dict):
    name = params.get("name", "")
    if not name:
        return "Export cancelled"
    path = os.path.join(PRESETS_DIR, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(params.get("values", {}), f, ensure_ascii=False, indent=4)
    return "Preset exported successfully!"


# ═══════════════════════════════════════════════════════════════════════════
# Launch
# ═══════════════════════════════════════════════════════════════════════════
def get_port_from_args():
    if "--port" in sys.argv:
        port_index = sys.argv.index("--port") + 1
        if port_index < len(sys.argv):
            return int(sys.argv[port_index])
    return DEFAULT_PORT


if __name__ == "__main__":
    port = get_port_from_args()
    app.launch(
        server_port=port,
        share="--share" in sys.argv,
        inbrowser="--open" in sys.argv,
        show_error=True,
    )
