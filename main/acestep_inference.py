"""
ACE-Step Music Generation Integration for Hyper-RVC.

Provides a backend wrapper for ACE-Step 1.5 inference, including:
- Lazy initialization of DiT (audio generation) and LM (reasoning) handlers
- Text-to-music generation
- Cover (style transfer) generation
- Repaint (segment editing) generation
- Model management (load, unload, list available models)
- Output directory management

This module is designed to be called from the Gradio tab (tabs/acestep_tab.py).
"""

import os
import sys
import torch
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime

now_dir = os.getcwd()
sys.path.append(now_dir)

from main.tools.logger import get_logger
from main.tools.variables import ACESTEP_OUTPUT_DIR, get_acestep_defaults

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Global state – handlers are lazily initialised on first use
# ---------------------------------------------------------------------------

_dit_handler = None
_llm_handler = None
_handlers_initialized = False


def _ensure_output_dir() -> str:
    """Create and return the output directory for ACE-Step generations."""
    os.makedirs(ACESTEP_OUTPUT_DIR, exist_ok=True)
    return ACESTEP_OUTPUT_DIR


# ---------------------------------------------------------------------------
# Model availability helpers
# ---------------------------------------------------------------------------

def get_available_dit_models() -> List[str]:
    """Return a list of locally available DiT model config names.

    Returns an empty list if the acestep package is not installed.
    """
    try:
        from acestep.handler import AceStepHandler
        handler = AceStepHandler()
        return handler.get_available_acestep_v15_models() or []
    except Exception as e:
        logger.error(f"Failed to list DiT models: {e}")
        return []


def get_available_lm_models() -> List[str]:
    """Return a list of locally available LM model paths.

    Returns an empty list if the acestep package is not installed.
    """
    try:
        from acestep.llm_inference import LLMHandler
        handler = LLMHandler()
        return handler.get_available_5hz_lm_models() or []
    except Exception as e:
        logger.error(f"Failed to list LM models: {e}")
        return []


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

def initialize_handlers(
    dit_model: str = None,
    lm_model: str = None,
    lm_backend: str = None,
    device: str = None,
    use_lm: bool = None,
) -> Tuple[str, str]:
    """Initialize (or re-initialize) the DiT and optionally the LM handler.

    Args:
        dit_model:    DiT model config name or path (e.g. ``"acestep-v15-turbo"``).
        lm_model:     LM model checkpoint name (e.g. ``"acestep-5Hz-lm-0.6B"``).
        lm_backend:   LM inference backend (``"vllm"``, ``"pytorch"``, ``"mlx"``).
        device:       Target device (``"auto"``, ``"cuda"``, ``"cpu"``, ``"mps"``).
        use_lm:       Whether to load the LM handler.

    Returns:
        Tuple of ``(status_message, detail)`` where *detail* contains extra info.
    """
    global _dit_handler, _llm_handler, _handlers_initialized

    # Apply defaults from variables.py
    _defaults = get_acestep_defaults()
    if dit_model is None:
        dit_model = _defaults["dit_model"]
    if lm_model is None:
        lm_model = _defaults["lm_model"]
    if lm_backend is None:
        lm_backend = _defaults["lm_backend"]
    if device is None:
        device = _defaults["device"]
    if use_lm is None:
        use_lm = _defaults["use_lm"]

    from main.acestep.handler import AceStepHandler
    from main.acestep.llm_inference import LLMHandler
  
    # Resolve device
    if device == "auto":
        if torch.cuda.is_available():
            resolved = "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            resolved = "mps"
        else:
            resolved = "cpu"
    else:
        resolved = device

    # ---- DiT handler ----
    try:
        logger.info(f"Initializing DiT handler: model={dit_model}, device={resolved}")
        if _dit_handler is not None:
            # Allow hot-swap by re-creating
            del _dit_handler
            _dit_handler = None
            torch.cuda.empty_cache()

        _dit_handler = AceStepHandler()
        _dit_handler.initialize_service(
            project_root=now_dir,
            config_path=dit_model,
            device=resolved,
        )
        logger.info("DiT handler initialized successfully.")
    except Exception as e:
        logger.error(f"DiT initialization failed: {e}")
        _dit_handler = None
        return f"DiT initialization failed: {e}", ""

    # ---- LM handler (optional) ----
    if use_lm:
        try:
            logger.info(f"Initializing LM handler: model={lm_model}, backend={lm_backend}, device={resolved}")
            if _llm_handler is not None:
                del _llm_handler
                _llm_handler = None
                torch.cuda.empty_cache()

            _llm_handler = LLMHandler()
            _llm_handler.initialize(
                checkpoint_dir=now_dir,
                lm_model_path=lm_model,
                backend=lm_backend,
                device=resolved,
            )
            logger.info("LM handler initialized successfully.")
        except Exception as e:
            logger.warning(f"LM initialization failed (continuing without LM): {e}")
            _llm_handler = None
            _handlers_initialized = True
            return f"DiT OK, LM failed ({e}). Running without LM reasoning.", resolved
    else:
        _llm_handler = None

    _handlers_initialized = True
    model_info = f"DiT={dit_model}"
    if use_lm:
        model_info += f", LM={lm_model}"
    return f"Models loaded: {model_info} on {resolved}", resolved


def unload_handlers() -> str:
    """Unload both handlers and free GPU memory."""
    global _dit_handler, _llm_handler, _handlers_initialized

    _dit_handler = None
    _llm_handler = None
    _handlers_initialized = False

    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return "Models unloaded. GPU memory freed."


def is_initialized() -> bool:
    """Return True if the DiT handler has been loaded."""
    return _handlers_initialized and _dit_handler is not None


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------

def run_acestep_inference(
    # Task
    task_type: str = "text2music",
    # Text inputs
    caption: str = "",
    lyrics: str = "",
    instrumental: bool = False,
    # Metadata
    bpm: Optional[int] = None,
    keyscale: str = "",
    timesignature: str = "",
    vocal_language: str = "unknown",
    duration: float = -1.0,
    # Audio inputs (cover / repaint)
    src_audio: Optional[str] = None,
    reference_audio: Optional[str] = None,
    audio_cover_strength: float = 1.0,
    repainting_start: float = 0.0,
    repainting_end: float = -1.0,
    # Generation parameters
    inference_steps: int = 8,
    guidance_scale: float = 7.0,
    seed: int = -1,
    batch_size: int = 2,
    # LM settings
    thinking: bool = True,
    lm_temperature: float = 0.85,
    # Output
    audio_format: str = "flac",
) -> Tuple[str, Optional[str]]:
    """Run ACE-Step music generation.

    Returns:
        Tuple of ``(status_message, output_audio_path)``.
        *output_audio_path* points to the first generated file (or None on failure).
    """
    global _dit_handler, _llm_handler

    if not is_initialized():
        return "Error: Models not loaded. Please load a model first.", None

    try:
        from acestep.inference import GenerationParams, GenerationConfig, generate_music
    except ImportError as exc:
        return f"Error: ACE-Step not installed ({exc})", None

    # Build GenerationParams
    params = GenerationParams(
        task_type=task_type,
        caption=caption or "",
        lyrics=lyrics or ("[Instrumental]" if instrumental else ""),
        instrumental=instrumental,
        bpm=bpm,
        keyscale=keyscale,
        timesignature=timesignature,
        vocal_language=vocal_language,
        duration=duration,
        reference_audio=reference_audio,
        src_audio=src_audio,
        audio_cover_strength=audio_cover_strength,
        repainting_start=repainting_start,
        repainting_end=repainting_end,
        inference_steps=inference_steps,
        guidance_scale=guidance_scale,
        seed=seed,
        thinking=thinking and _llm_handler is not None,
        lm_temperature=lm_temperature,
    )

    # Build GenerationConfig
    config = GenerationConfig(
        batch_size=batch_size,
        audio_format=audio_format,
    )

    save_dir = _ensure_output_dir()

    try:
        result = generate_music(
            dit_handler=_dit_handler,
            llm_handler=_llm_handler,
            params=params,
            config=config,
            save_dir=save_dir,
        )

        if not result.success:
            err = result.error or "Unknown error"
            return f"Generation failed: {err}", None

        # Return info about the first audio
        if result.audios:
            first = result.audios[0]
            path = first.get("path", "")
            n = len(result.audios)
            msg = f"Generated {n} audio(s)"
            if path:
                msg += f". First: {os.path.basename(path)}"
            msg += f"\n{result.status_message}"
            return msg, path

        return "Generation completed but no audio files produced.", None

    except Exception as e:
        logger.error(f"ACE-Step inference error: {e}")
        return f"Inference error: {e}", None


# ---------------------------------------------------------------------------
# Simple mode – LM auto-generates caption & lyrics from a description
# ---------------------------------------------------------------------------

def run_acestep_simple_mode(
    query: str = "",
    vocal_language: str = "en",
    duration: float = -1.0,
    inference_steps: int = 8,
    seed: int = -1,
    batch_size: int = 2,
    audio_format: str = "flac",
) -> Tuple[str, Optional[str]]:
    """Run ACE-Step in simple mode (LM auto-generates caption + lyrics).

    Returns:
        Tuple of ``(status_message, output_audio_path)``.
    """
    global _dit_handler, _llm_handler

    if not is_initialized():
        return "Error: Models not loaded. Please load a model first.", None

    if not _llm_handler or not _llm_handler.llm_initialized:
        return "Error: LM handler required for simple mode. Enable LM and reload.", None

    try:
        from acestep.inference import create_sample, GenerationParams, GenerationConfig, generate_music
    except ImportError as exc:
        return f"Error: ACE-Step not installed ({exc})", None

    if not query or not query.strip():
        return "Error: Please provide a description of the music you want.", None

    # Step 1: Let LM expand the query into caption + lyrics + metadata
    try:
        sample = create_sample(
            llm_handler=_llm_handler,
            query=query.strip(),
            vocal_language=vocal_language,
        )
    except Exception as e:
        return f"LM sample generation failed: {e}", None

    if not sample.success:
        err = sample.error or "Unknown error"
        return f"Sample generation failed: {err}", None

    caption = sample.caption or ""
    lyrics = sample.lyrics or "[Instrumental]"
    bpm_val = sample.bpm
    duration_val = sample.duration if sample.duration and sample.duration > 0 else duration
    key_val = sample.keyscale or ""

    # Step 2: Generate music with the expanded prompt
    params = GenerationParams(
        task_type="text2music",
        caption=caption,
        lyrics=lyrics,
        bpm=bpm_val,
        keyscale=key_val,
        vocal_language=vocal_language,
        duration=duration_val,
        inference_steps=inference_steps,
        seed=seed,
        thinking=False,  # Already used LM for sample creation
    )

    config = GenerationConfig(
        batch_size=batch_size,
        audio_format=audio_format,
    )

    save_dir = _ensure_output_dir()

    try:
        result = generate_music(
            dit_handler=_dit_handler,
            llm_handler=_llm_handler,
            params=params,
            config=config,
            save_dir=save_dir,
        )

        if not result.success:
            return f"Generation failed: {result.error}", None

        if result.audios:
            first = result.audios[0]
            path = first.get("path", "")
            n = len(result.audios)
            msg = f"Generated {n} audio(s)"
            if path:
                msg += f". First: {os.path.basename(path)}"
            # Show what the LM generated
            if caption:
                msg += f"\nCaption: {caption[:120]}..."
            return msg, path

        return "Generation completed but no audio files produced.", None

    except Exception as e:
        logger.error(f"ACE-Step simple mode error: {e}")
        return f"Inference error: {e}", None


# ---------------------------------------------------------------------------
# Get generated output files
# ---------------------------------------------------------------------------

def get_output_files() -> List[str]:
    """Return a list of recently generated audio files."""
    if not os.path.isdir(ACESTEP_OUTPUT_DIR):
        return []
    valid_ext = {".flac", ".wav", ".mp3", ".ogg", ".opus", ".aac"}
    files = []
    for f in sorted(os.listdir(ACESTEP_OUTPUT_DIR), reverse=True):
        if os.path.splitext(f)[1].lower() in valid_ext:
            files.append(os.path.join(ACESTEP_OUTPUT_DIR, f))
    return files


def clear_output_files() -> str:
    """Delete all generated audio files."""
    import shutil
    if os.path.isdir(ACESTEP_OUTPUT_DIR):
        shutil.rmtree(ACESTEP_OUTPUT_DIR)
        os.makedirs(ACESTEP_OUTPUT_DIR, exist_ok=True)
        return "Output files cleared."
    return "No output files to clear."
