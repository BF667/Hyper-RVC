"""
Hyper-RVC main package.

Provides a modular architecture for:
- Audio separation (UVR / music separation)
- RVC voice conversion
- Text-to-Speech (Edge TTS + RVC)
- Whisper transcription
- Audio effects and processing
- File utilities and model downloading

This package re-exports key functions for backward compatibility
with code that previously imported from ``core.py``.
"""

import sys
import os

# Python 3.13+ removed the audioop module; pydub depends on it.
# Provide a transparent shim so pydub keeps working.
if sys.version_info >= (3, 13):
    try:
        import audioop  # noqa: F401
    except ImportError:
        import audioop_lts as audioop  # noqa: F401
        sys.modules["audioop"] = audioop

now_dir = os.getcwd()
sys.path.append(now_dir)

# ---------------------------------------------------------------------------
# Backward-compatible re-exports from sub-modules
# ---------------------------------------------------------------------------

from main.tools.file_utils import (  # noqa: E402, F401
    get_last_modified_file,
    search_with_word,
    search_with_two_words,
    get_last_modified_folder,
    get_model_info_by_name,
    download_file,
)

from main.tools.audio_utils import (  # noqa: E402, F401
    add_audio_effects,
    merge_audios,
    update_model_config_for_fp16,
)

from main.tools.downloader import (  # noqa: E402, F401
    download_model,
    download_music,
)

from main.utils import (  # noqa: E402, F401
    download_all_pipeline,
    download_acestep_models,
    download_predictor,
)

from main.rvc.converter import (  # noqa: E402, F401
    import_voice_converter,
    get_config,
    run_rvc_conversion,
)

from main.tts.synthesis import (  # noqa: E402, F401
    EDGE_TTS_VOICES,
    TTS_RATE_OPTIONS,
    run_edge_tts,
    run_tts_inference,
    get_tts_voices,
    get_tts_languages,
    get_tts_rate_options,
)

from main.whisper.transcriber import whisper_process  # noqa: E402, F401

from main.acestep_inference import (  # noqa: E402, F401
    initialize_handlers,
    unload_handlers,
    is_initialized,
    run_acestep_inference,
    run_acestep_simple_mode,
    get_available_dit_models,
    get_available_lm_models,
    get_output_files,
    clear_output_files,
)

__all__ = [
    # file_utils
    "get_last_modified_file",
    "search_with_word",
    "search_with_two_words",
    "get_last_modified_folder",
    "get_model_info_by_name",
    "download_file",
    # audio_utils
    "add_audio_effects",
    "merge_audios",
    "update_model_config_for_fp16",
    # downloader
    "download_model",
    "download_music",
    # utils
    "download_all_pipeline",
    "download_acestep_models",
    "download_predictor",
    # rvc
    "import_voice_converter",
    "get_config",
    "run_rvc_conversion",
    # tts
    "EDGE_TTS_VOICES",
    "TTS_RATE_OPTIONS",
    "run_edge_tts",
    "run_tts_inference",
    "get_tts_voices",
    "get_tts_languages",
    "get_tts_rate_options",
    # whisper
    "whisper_process",
    # acestep
    "initialize_handlers",
    "unload_handlers",
    "is_initialized",
    "run_acestep_inference",
    "run_acestep_simple_mode",
    "get_available_dit_models",
    "get_available_lm_models",
    "get_output_files",
    "clear_output_files",
]
