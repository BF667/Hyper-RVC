"""
Download utilities for Hyper-RVC.

Provides high-level download helpers for:
- RVC voice models (multi-source, with method selection)
- Music from YouTube and other supported sites (via yt-dlp)

Supported download methods:
- auto        – Auto-detect from URL pattern
- gdrive      – Google Drive (gdown)
- huggingface – HuggingFace (/blob/, /resolve/, /tree/)
- mediafire   – MediaFire
- pixeldrain  – PixelDrain
- yandex      – Yandex Disk
- discord     – Discord CDN
- applio      – Applio.org model registry
- direct      – Any direct URL (requests streaming)
"""

import os
import re
import sys
import shutil
import zipfile
import subprocess
from urllib.parse import unquote, urlencode, parse_qs, urlparse

from tqdm import tqdm
import requests

now_dir = os.getcwd()
sys.path.append(now_dir)

from main.tools.logger import get_logger

logger = get_logger(__name__)

# -- Paths ----------------------------------------------------------------

_logs_root = os.path.join(now_dir, "logs")
_zips_path = os.path.join(_logs_root, "zips")


def _ensure_zips_dir():
    os.makedirs(_zips_path, exist_ok=True)


# ===================================================================
# Method detection
# ===================================================================

DOWNLOAD_METHODS = [
    "auto",
    "gdrive",
    "huggingface",
    "mediafire",
    "pixeldrain",
    "yandex",
    "discord",
    "applio",
    "direct",
]


def detect_method(url: str) -> str:
    """Auto-detect the best download method from a URL."""
    if not url:
        return "direct"
    u = url.lower().strip()
    if "drive.google.com" in u:
        return "gdrive"
    if "huggingface.co" in u:
        return "huggingface"
    if "mediafire.com" in u:
        return "mediafire"
    if "pixeldrain.com" in u:
        return "pixeldrain"
    if "disk.yandex.ru" in u:
        return "yandex"
    if "cdn.discordapp.com" in u or "media.discordapp.net" in u:
        return "discord"
    if "applio.org" in u:
        return "applio"
    return "direct"


# ===================================================================
# Streaming download helper (large chunks, tqdm)
# ===================================================================

_CHUNK_SIZE = 8 * 1024 * 1024  # 8 MB chunks for speed


def _stream_download(url, dest_path, desc=None):
    """Stream-download a file with a tqdm progress bar (8 MB chunks)."""
    resp = requests.get(url, stream=True, timeout=30)
    resp.raise_for_status()

    total = int(resp.headers.get("content-length", 0))
    os.makedirs(os.path.dirname(dest_path) or ".", exist_ok=True)

    bar = tqdm(
        total=total or None,
        unit="B",
        unit_scale=True,
        desc=desc or os.path.basename(dest_path),
        ncols=80,
        colour="CYAN",
        mininterval=0.1,
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
    )
    with open(dest_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=_CHUNK_SIZE):
            if chunk:
                f.write(chunk)
                bar.update(len(chunk))
    bar.close()
    return dest_path


# ===================================================================
# Per-method downloaders
# ===================================================================

def _download_gdrive(url, dest_dir):
    """Download from Google Drive via gdown."""
    from main.tools import gdown

    # Extract file ID
    if "file/d/" in url:
        file_id = url.split("file/d/")[1].split("/")[0]
    elif "id=" in url:
        file_id = url.split("id=")[1].split("&")[0]
    else:
        raise ValueError("Cannot parse Google Drive file ID from URL")

    _ensure_zips_dir()
    try:
        output = gdown.download(
            f"https://drive.google.com/uc?id={file_id}",
            output=dest_dir,
            quiet=False,
            fuzzy=True,
        )
        return output
    except Exception as e:
        err = str(e)
        if "Too many users" in err:
            raise RuntimeError("Google Drive download quota exceeded. Try again later or use a different link.")
        if "Cannot retrieve the public link" in err:
            raise RuntimeError("Private or restricted Google Drive link. Make sure the file is publicly accessible.")
        raise


def _download_huggingface(url, dest_dir):
    """Download from HuggingFace (blob, resolve, tree)."""
    from main.tools.hf import HF_download_file

    # Handle /tree/ URLs (repo tree pages) – look for a .zip link
    if "/tree/" in url:
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            # Try to find a zip download link
            zip_match = re.search(r'href="([^"]+\.zip)"', resp.text)
            if zip_match:
                zip_url = zip_match.group(1)
                if not zip_url.startswith("http"):
                    zip_url = "https://huggingface.co" + zip_url
                zip_url = zip_url.replace("/blob/", "/resolve/")
                return _stream_download(zip_url, os.path.join(dest_dir, "model.zip"), desc="HuggingFace tree")
        except Exception:
            pass
        raise RuntimeError("Could not find a downloadable .zip file on the HuggingFace page.")

    # Normal /blob/ or /resolve/
    clean_url = url.replace("/blob/", "/resolve/").replace("?download=true", "")
    return HF_download_file(clean_url, dest_dir)


def _download_mediafire(url, dest_dir):
    """Download from MediaFire."""
    from main.tools.mediafire import Mediafire_Download
    return Mediafire_Download(url, output=dest_dir)


def _download_pixeldrain(url, dest_dir):
    """Download from PixelDrain."""
    file_id = url.rstrip("/").split("/")[-1]
    api_url = f"https://pixeldrain.com/api/file/{file_id}"

    resp = requests.get(api_url, stream=True, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"PixelDrain returned HTTP {resp.status_code}")

    filename = "model.zip"
    cd = resp.headers.get("Content-Disposition", "")
    fname_match = re.search(r'filename="?([^";\n]+)"?', cd)
    if fname_match:
        filename = fname_match.group(1).strip('"')

    dest = os.path.join(dest_dir, filename)
    return _stream_download(api_url, dest, desc=filename)


def _download_yandex(url, dest_dir):
    """Download from Yandex Disk."""
    base_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download?"
    final_url = base_url + urlencode(dict(public_key=url))
    resp = requests.get(final_url, timeout=15)
    resp.raise_for_status()
    download_url = resp.json()["href"]

    filename = "model.zip"
    parsed = parse_qs(urlparse(unquote(download_url)).query)
    if parsed.get("filename"):
        filename = parsed["filename"][0]

    dest = os.path.join(dest_dir, filename)
    return _stream_download(download_url, dest, desc=filename)


def _download_discord(url, dest_dir):
    """Download from Discord CDN."""
    filename = url.rstrip("/").split("/")[-1].split("?")[0]
    dest = os.path.join(dest_dir, filename)
    return _stream_download(url, dest, desc=filename)


def _download_applio(url, dest_dir):
    """Download from Applio.org model registry."""
    parts = url.split("/")
    id_with_query = parts[-1]
    id_number = id_with_query.split("?")[0]

    api_url = "https://cjtfqzjfdimgpvpwhzlv.supabase.co/rest/v1/models"
    headers = {
        "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNqdGZxempmZGltZ3B2cHdoemx2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE2OTUxNjczODgsImV4cCI6MjAxMDc0MzM4OH0.7z5WMIbjR99c2Ooc0ma7B_FyGq10G8X-alkCYTkKR10"
    }
    params = {"id": f"eq.{id_number}"}

    resp = requests.get(api_url, headers=headers, params=params, timeout=15)
    if resp.status_code != 200 or not resp.json():
        raise RuntimeError("Could not find model on Applio. Check the URL.")

    real_link = resp.json()[0]["link"]
    method = detect_method(real_link)
    return _download_by_method(real_link, method, dest_dir)


def _download_direct(url, dest_dir):
    """Download any direct URL with streaming."""
    filename = "model.zip"
    cd = ""
    try:
        head = requests.head(url, allow_redirects=True, timeout=10)
        cd = head.headers.get("Content-Disposition", "")
    except Exception:
        pass

    fname_match = re.search(r'filename="?([^";\n]+)"?', cd)
    if fname_match:
        filename = fname_match.group(1).strip('"').replace(os.path.sep, "_")
    else:
        url_basename = url.rstrip("/").split("/")[-1].split("?")[0]
        if url_basename and "." in url_basename:
            filename = url_basename

    dest = os.path.join(dest_dir, filename)
    return _stream_download(url, dest, desc=filename)


# ===================================================================
# Method dispatcher
# ===================================================================

_METHOD_MAP = {
    "gdrive": _download_gdrive,
    "huggingface": _download_huggingface,
    "mediafire": _download_mediafire,
    "pixeldrain": _download_pixeldrain,
    "yandex": _download_yandex,
    "discord": _download_discord,
    "applio": _download_applio,
    "direct": _download_direct,
}


def _download_by_method(url, method, dest_dir):
    """Dispatch to the correct downloader by method name."""
    fn = _METHOD_MAP.get(method)
    if fn is None:
        raise ValueError(f"Unknown download method: {method}")
    return fn(url, dest_dir)


# ===================================================================
# Post-download: extract zip into logs/
# ===================================================================

def _extract_zip_to_logs(zip_path):
    """Extract a zip file into the logs/ directory and clean up.

    Returns the model folder path, or None on error.
    """
    from main.rvc.engine.lib.utils import format_title

    if not os.path.isfile(zip_path):
        return None

    model_zip = os.path.basename(zip_path)
    model_name = format_title(model_zip.rsplit(".zip", 1)[0])
    extract_path = os.path.join(_logs_root, os.path.normpath(model_name))

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_path)
    except zipfile.BadZipFile:
        return None

    os.remove(zip_path)

    # Remove macOS metadata
    macosx = os.path.join(extract_path, "__MACOSX")
    if os.path.isdir(macosx):
        shutil.rmtree(macosx)

    # Flatten single sub-folder
    subfolders = [
        f for f in os.listdir(extract_path)
        if os.path.isdir(os.path.join(extract_path, f))
    ]
    if len(subfolders) == 1:
        sub = os.path.join(extract_path, subfolders[0])
        for item in os.listdir(sub):
            shutil.move(os.path.join(sub, item), os.path.join(extract_path, item))
        os.rmdir(sub)

    # Rename .pth to match folder name
    for item in os.listdir(extract_path):
        if item.endswith(".pth"):
            stem = item.rsplit(".pth", 1)[0]
            if stem != model_name:
                os.rename(
                    os.path.join(extract_path, item),
                    os.path.join(extract_path, model_name + ".pth"),
                )
        elif item.endswith(".index"):
            # Keep index naming as-is (already handled by format_title)
            pass

    return extract_path


# ===================================================================
# Public API
# ===================================================================

def download_model(link: str, method: str = "auto") -> str:
    """
    Download an RVC model from a link.

    Supports multiple sources via the *method* parameter or auto-detection.

    Args:
        link: URL to download the model from.
        method: One of ``auto``, ``gdrive``, ``huggingface``, ``mediafire``,
            ``pixeldrain``, ``yandex``, ``discord``, ``applio``, ``direct``.
            Defaults to ``auto``.

    Returns:
        Success message, or an error description on failure.
    """
    if not link or not link.strip():
        return "Error: No URL provided"

    link = link.strip()
    _ensure_zips_dir()

    # Resolve method
    if method == "auto":
        method = detect_method(link)

    logger.info(f"Downloading model from {link} (method: {method})")

    try:
        result = _download_by_method(link, method, _zips_path)

        # result can be a filepath string or None
        if result is None:
            return f"Error: Download returned no file (method: {method})"

        # If result is not in zips_path, copy it there
        if not os.path.dirname(result) == _zips_path:
            dest = os.path.join(_zips_path, os.path.basename(result))
            shutil.copy2(result, dest)
            result = dest

        # Try to extract if it's a zip
        if result.endswith(".zip"):
            extracted = _extract_zip_to_logs(result)
            if extracted:
                return f"Model downloaded and extracted successfully to: {extracted}"
            else:
                return f"Model downloaded to: {result} (failed to extract)"
        else:
            return f"Model downloaded to: {result}"

    except Exception as e:
        logger.error(f"Error downloading model: {e}")
        return f"Error: {e}"


def download_music(link: str) -> str:
    """
    Download music from a URL (YouTube, etc.) as an audio file.

    Uses ``yt-dlp`` to extract the audio stream and saves it to
    ``audio_files/original_files/``.

    Args:
        link: URL to download music from

    Returns:
        Success message string, or an error description on failure
    """
    try:
        os.makedirs(os.path.join(now_dir, "audio_files", "original_files"), exist_ok=True)
        command = [
            "yt-dlp",
            "-x",
            "--output",
            os.path.join(now_dir, "audio_files", "original_files", "%(title)s.%(ext)s"),
            link,
        ]
        subprocess.run(command, check=True)
        logger.info("Music downloaded successfully")
        return "Music downloaded with success"
    except subprocess.CalledProcessError as e:
        logger.error(f"Error downloading music: {e}")
        return f"Error downloading music: {e}"
    except Exception as e:
        logger.error(f"Unexpected error downloading music: {e}")
        return f"Error downloading music: {e}"
