"""
Backward-compatible shim for Hyper-RVC core module.

All functionality has been moved to the ``main`` package.  This module
re-exports everything so that existing code (tabs, CLI, third-party scripts)
that does ``from core import ...`` continues to work without changes.

New code should import directly from ``main`` or its sub-modules:

- ``from main.core import full_inference_program``
- ``from main.uvr.separator import separate_vocals``
- ``from main.rvc.converter import run_rvc_conversion``
- ``from main.tts.synthesis import run_tts_inference``
- ``from main.whisper.transcriber import whisper_process``
- ``from main.tools.file_utils import search_with_word``
- ``from main.tools.audio_utils import add_audio_effects``
- ``from main.tools.downloader import download_model``
"""

# Re-export everything from the main package
from main import *  # noqa: F401, F403
from main.core import full_inference_program  # noqa: F401
