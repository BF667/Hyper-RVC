"""
main.tts – Text-to-Speech sub-package.

Wraps Microsoft Edge TTS and optionally chains it with RVC voice
conversion for a complete text → speech pipeline.
"""

from main.tts.synthesis import (  # noqa: F401
    EDGE_TTS_VOICES,
    TTS_RATE_OPTIONS,
    run_edge_tts,
    run_tts_inference,
    get_tts_voices,
    get_tts_languages,
    get_tts_rate_options,
)
