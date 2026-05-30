"""
File search and management utilities for Hyper-RVC.

Provides helpers for locating audio files by name patterns, resolving model
metadata, and downloading model artefacts from remote URLs.
"""

import os
import sys
import torch
from typing import Optional, Dict, Any

now_dir = os.getcwd()
sys.path.append(now_dir)

from main.tools.variables import (
    models_vocals,
    karaoke_models,
    denoise_models,
    deecho_models,
    dereverb_models,
)
from main.tools.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Directory / file search helpers
# ---------------------------------------------------------------------------

def get_last_modified_file(pasta: str) -> Optional[str]:
    """
    Get the most recently modified file in a directory.

    Args:
        pasta: Directory path to search

    Returns:
        Name of the most recently modified file, or None if directory is
        empty or does not exist
    """
    if not os.path.isdir(pasta):
        return None
    arquivos = [f for f in os.listdir(pasta) if os.path.isfile(os.path.join(pasta, f))]
    if not arquivos:
        return None
    return max(arquivos, key=lambda x: os.path.getmtime(os.path.join(pasta, x)))


def search_with_word(folder: str, word: str) -> Optional[str]:
    """
    Search for the most recent file containing a specific word in its name.

    Args:
        folder: Directory to search in
        word: Word to search for in filenames

    Returns:
        Name of the most recent file containing the word, or None if
        not found or directory does not exist
    """
    if not os.path.isdir(folder):
        return None
    file_with_word = [file for file in os.listdir(folder) if word in file]
    if not file_with_word:
        return None
    most_recent_file = max(
        file_with_word, key=lambda file: os.path.getmtime(os.path.join(folder, file))
    )
    return most_recent_file


def search_with_two_words(folder: str, word1: str, word2: str) -> Optional[str]:
    """
    Search for the most recent file containing two specific words in its name.

    Args:
        folder: Directory to search in
        word1: First word to search for
        word2: Second word to search for

    Returns:
        Name of the most recent file containing both words, or None if
        not found or directory does not exist
    """
    if not os.path.isdir(folder):
        return None
    file_with_words = [
        file for file in os.listdir(folder) if word1 in file and word2 in file
    ]
    if not file_with_words:
        return None
    most_recent_file = max(
        file_with_words, key=lambda file: os.path.getmtime(os.path.join(folder, file))
    )
    return most_recent_file


def get_last_modified_folder(path: str) -> Optional[str]:
    """
    Get the most recently modified subdirectory.

    Args:
        path: Parent directory path

    Returns:
        Path to the most recently modified subdirectory, or None if none exist
    """
    directories = [
        os.path.join(path, d)
        for d in os.listdir(path)
        if os.path.isdir(os.path.join(path, d))
    ]
    if not directories:
        return None
    last_modified_folder = max(directories, key=os.path.getmtime)
    return last_modified_folder


# ---------------------------------------------------------------------------
# Model helpers
# ---------------------------------------------------------------------------

def get_model_info_by_name(model_name: str) -> Optional[Dict[str, Any]]:
    """
    Get model information by model name.

    Searches through all known model categories (vocals, karaoke, dereverb,
    deecho, denoise) and returns the first match.

    Args:
        model_name: Name of the model to search for

    Returns:
        Dictionary containing model information, or None if not found
    """
    all_models = (
        models_vocals
        + karaoke_models
        + dereverb_models
        + deecho_models
        + denoise_models
    )
    for model in all_models:
        if model["name"] == model_name:
            return model
    return None


# ---------------------------------------------------------------------------
# Download helpers
# ---------------------------------------------------------------------------

def download_file(url: str, path: str, filename: str) -> Optional[str]:
    """
    Download a file from a URL to a specified path.

    Skips the download if the file already exists at the target location.

    Args:
        url: URL to download from
        path: Directory path to save the file
        filename: Name of the file to save

    Returns:
        Path to downloaded file if successful, None otherwise
    """
    os.makedirs(path, exist_ok=True)
    file_path = os.path.join(path, filename)

    if os.path.exists(file_path):
        logger.info(f"File '{filename}' already exists at '{path}'.")
        return file_path

    try:
        torch.hub.download_url_to_file(url, file_path)
        logger.info(f"File '{filename}' downloaded successfully")
        return file_path
    except Exception as e:
        logger.error(f"Error downloading file '{filename}' from '{url}': {e}")
        return None
