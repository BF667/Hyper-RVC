"""
General-purpose utilities for Hyper-RVC.

This module contains helper functions used across multiple subsystems,
including auto-downloading F0 predictor models and embedder weights
when they are missing.

All download config (URLs, file lists, folder mappings) lives in
``main/tools/variables.py`` — this module only contains the download
logic itself.
"""

import os
import sys
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import requests

# Ensure the project root is on sys.path when run directly
_now_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _now_dir not in sys.path:
    sys.path.insert(0, _now_dir)

from main.tools.variables import (
    PREDICTORS_URL_BASE,
    EMBEDDERS_URL_BASE,
    predictors_list,
    embedders_list,
    download_folder_mapping,
    configs,
)

# All download sources combined for the unified pipeline
_all_sources = [
    (PREDICTORS_URL_BASE, predictors_list),
    (EMBEDDERS_URL_BASE, embedders_list),
]


# ===================================================================
# Low-level helpers
# ===================================================================

def _download_file(url, destination_path, global_bar):
    """Download a single file while updating the global progress bar."""
    dir_name = os.path.dirname(destination_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    response = requests.get(url, stream=True)
    block_size = 1024
    with open(destination_path, "wb") as file:
        for data in response.iter_content(block_size):
            file.write(data)
            global_bar.update(len(data))


def _collect_missing(file_list, url_base, folder_mapping):
    """Return list of (url, destination_path) for files not yet downloaded."""
    missing = []
    for remote_folder, files in file_list:
        local_folder = folder_mapping.get(remote_folder, "")
        for file in files:
            destination_path = os.path.join(local_folder, file)
            if not os.path.exists(destination_path):
                missing.append((f"{url_base}/{file}", destination_path))
    return missing


# ===================================================================
# Single-file predictor auto-download
# ===================================================================

def download_predictor(predictor):
    """Download a single predictor model file if it does not already exist.

    Checks whether *predictor* exists inside the configured predictors
    directory.  If it is missing, the file is fetched from the HuggingFace
    repository ``NeoPy/Ultimate-Models``.

    Args:
        predictor (str): Filename of the predictor model, e.g.
            ``"rmvpe.pt"``, ``"crepe.onnx"``, ``"fcpe.pt"``.

    Returns:
        bool: ``True`` if the file exists after the call (either it was
        already present or it was downloaded successfully), ``False``
        otherwise.
    """
    from main.tools.hf import HF_download_file

    model_path = os.path.join(configs["predictors_path"], predictor)

    if not os.path.exists(model_path):
        HF_download_file(
            PREDICTORS_URL_BASE + "/" + predictor,
            model_path,
        )

    return os.path.exists(model_path)


# ===================================================================
# Bulk download pipeline — single progress bar
# ===================================================================

def download_all_pipeline():
    """Download all missing predictors + embedders with a single progress bar."""
    # Collect every missing file across all sources
    all_missing = []
    for url_base, file_list in _all_sources:
        all_missing.extend(_collect_missing(file_list, url_base, download_folder_mapping))

    if not all_missing:
        return

    # Quick HEAD-scan for total size
    total_size = 0
    sizes = []
    for url, _ in all_missing:
        try:
            resp = requests.head(url, timeout=10)
            size = int(resp.headers.get("content-length", 0))
        except Exception:
            size = 0
        sizes.append(size)
        total_size += size

    with tqdm(
        total=total_size if total_size > 0 else None,
        unit="iB",
        unit_scale=True,
        desc="Downloading models",
        ncols=80,
        colour="GREEN",
        mininterval=1.0,
        smoothing=0.9,
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
    ) as bar:
        with ThreadPoolExecutor() as executor:
            futures = []
            for (url, dest), size in zip(all_missing, sizes):
                if size > 0:
                    futures.append(executor.submit(_download_file, url, dest, bar))
                else:
                    # Unknown size — download without byte-level tracking
                    futures.append(executor.submit(_download_file_no_size, url, dest))
            for future in futures:
                future.result()


def _download_file_no_size(url, destination_path):
    """Download a file without byte-level progress tracking."""
    dir_name = os.path.dirname(destination_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    response = requests.get(url, stream=True)
    with open(destination_path, "wb") as file:
        for chunk in response.iter_content(1024):
            file.write(chunk)


if __name__ == "__main__":
    download_all_pipeline()
