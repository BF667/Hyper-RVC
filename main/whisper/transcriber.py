"""
Whisper transcription module for Hyper-RVC.

Wraps OpenAI Whisper (via the project's ``main/whisper/diarization``
integration) to produce word-level or segment-level transcriptions that
can be fed into a queue for downstream processing (e.g. speaker
diarization).
"""

import os
import sys
import gc
from typing import Dict, Any, Optional

now_dir = os.getcwd()
sys.path.append(now_dir)

from main.tools.variables import check_fp16_support
from main.tools.logger import get_logger

logger = get_logger(__name__)


def whisper_process(
    model_size: str,
    input_audio: str,
    configs: Dict[str, Any],
    device: str,
    out_queue,
    word_timestamps: bool = True,
) -> None:
    """
    Process audio with Whisper for transcription / speaker diarization.

    The transcription segments are placed into *out_queue*.  If an
    exception occurs the exception object itself is placed into the queue
    so the consumer can handle it.

    Args:
        model_size:      Size of the Whisper model (e.g. ``"base"``,
                         ``"small"``, ``"medium"``, ``"large"``).
        input_audio:     Path to the input audio file.
        configs:         Configuration dictionary (currently unused but
                         kept for API compatibility).
        device:          Device string (``"cpu"``, ``"cuda"``, etc.).
        out_queue:       Queue to put transcription results into.
        word_timestamps: Whether to extract word-level timestamps.
    """
    from main.whisper.diarization.whisper import load_model

    try:
        segments = load_model(
            model_size,
            device=device,
        ).transcribe(
            input_audio,
            fp16=check_fp16_support(device),
            word_timestamps=word_timestamps,
        )

        out_queue.put(segments["segments"])
    except Exception as e:
        out_queue.put(e)
    finally:
        del segments
        gc.collect()
