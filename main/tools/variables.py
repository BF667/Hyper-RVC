"""
Variable definitions and configuration for Hyper-RVC.

Contains model definitions, FP16 support checking, and other global variables.
"""

import os
import torch
import sys

now_dir = os.getcwd()
sys.path.append(now_dir)

from main.tools.logger import get_logger

logger = get_logger(__name__)


# FP16 configuration
def check_fp16_support(device: str) -> bool:
    """
    Check if a device supports FP16 inference.

    Args:
        device: Device string (e.g., 'cuda:0', 'cpu')

    Returns:
        True if FP16 is supported, False otherwise
    """
    if device == "cpu":
        return False
    try:
        i_device = int(str(device).split(":")[-1])
        gpu_name = torch.cuda.get_device_name(i_device)
        low_end_gpus = ["16", "P40", "P10", "1060", "1070", "1080"]
        if any(gpu in gpu_name for gpu in low_end_gpus) and "V100" not in gpu_name.upper():
            logger.info(f"Your GPU {gpu_name} does not support FP16 inference. Using FP32 instead.")
            return False
        return True
    except Exception as e:
        logger.warning(f"Error checking FP16 support: {e}")
        return False

models_vocals = [
    {
        "name": "Mel-Roformer by KimberleyJSN",
        "path": os.path.join(now_dir, "models", "mel-vocals"),
        "model": os.path.join(now_dir, "models", "mel-vocals", "model.ckpt"),
        "config": os.path.join(now_dir, "models", "mel-vocals", "config.yaml"),
        "type": "mel_band_roformer",
        "config_url": "https://raw.githubusercontent.com/ZFTurbo/Music-Source-Separation-Training/main/configs/KimberleyJensen/config_vocals_mel_band_roformer_kj.yaml",
        "model_url": "https://huggingface.co/KimberleyJSN/melbandroformer/resolve/main/MelBandRoformer.ckpt",
    },
    {
        "name": "BS-Roformer by ViperX",
        "path": os.path.join(now_dir, "models", "bs-vocals"),
        "model": os.path.join(now_dir, "models", "bs-vocals", "model.ckpt"),
        "config": os.path.join(now_dir, "models", "bs-vocals", "config.yaml"),
        "type": "bs_roformer",
        "config_url": "https://raw.githubusercontent.com/ZFTurbo/Music-Source-Separation-Training/main/configs/viperx/model_bs_roformer_ep_317_sdr_12.9755.yaml",
        "model_url": "https://github.com/TRvlvr/model_repo/releases/download/all_public_uvr_models/model_bs_roformer_ep_317_sdr_12.9755.ckpt",
    },
    {
        "name": "MDX23C",
        "path": os.path.join(now_dir, "models", "mdx23c-vocals"),
        "model": os.path.join(now_dir, "models", "mdx23c-vocals", "model.ckpt"),
        "config": os.path.join(now_dir, "models", "mdx23c-vocals", "config.yaml"),
        "type": "mdx23c",
        "config_url": "https://raw.githubusercontent.com/ZFTurbo/Music-Source-Separation-Training/main/configs/config_vocals_mdx23c.yaml",
        "model_url": "https://github.com/ZFTurbo/Music-Source-Separation-Training/releases/download/v1.0.0/model_vocals_mdx23c_sdr_10.17.ckpt",
    },
]

karaoke_models = [
    {
        "name": "Mel-Roformer Karaoke by aufr33 and viperx",
        "path": os.path.join(now_dir, "models", "mel-kara"),
        "model": os.path.join(now_dir, "models", "mel-kara", "model.ckpt"),
        "config": os.path.join(now_dir, "models", "mel-kara", "config.yaml"),
        "type": "mel_band_roformer",
        "config_url": "https://huggingface.co/shiromiya/audio-separation-models/resolve/main/mel_band_roformer_karaoke_aufr33_viperx/config_mel_band_roformer_karaoke.yaml",
        "model_url": "https://huggingface.co/shiromiya/audio-separation-models/resolve/main/mel_band_roformer_karaoke_aufr33_viperx/mel_band_roformer_karaoke_aufr33_viperx_sdr_10.1956.ckpt",
    },
    {
        "name": "UVR-BVE",
        "full_name": "UVR-BVE-4B_SN-44100-1.pth",
        "arch": "vr",
    },
]

denoise_models = [
    {
        "name": "Mel-Roformer Denoise Normal by aufr33",
        "path": os.path.join(now_dir, "models", "mel-denoise"),
        "model": os.path.join(now_dir, "models", "mel-denoise", "model.ckpt"),
        "config": os.path.join(now_dir, "models", "mel-denoise", "config.yaml"),
        "type": "mel_band_roformer",
        "config_url": "https://huggingface.co/shiromiya/audio-separation-models/resolve/main/mel-denoise/model_mel_band_roformer_denoise.yaml",
        "model_url": "https://huggingface.co/jarredou/aufr33_MelBand_Denoise/resolve/main/denoise_mel_band_roformer_aufr33_sdr_27.9959.ckpt",
    },
    {
        "name": "Mel-Roformer Denoise Aggressive by aufr33",
        "path": os.path.join(now_dir, "models", "mel-denoise-aggr"),
        "model": os.path.join(now_dir, "models", "mel-denoise-aggr", "model.ckpt"),
        "config": os.path.join(now_dir, "models", "mel-denoise-aggr", "config.yaml"),
        "type": "mel_band_roformer",
        "config_url": "https://huggingface.co/shiromiya/audio-separation-models/resolve/main/mel-denoise/model_mel_band_roformer_denoise.yaml",
        "model_url": "https://huggingface.co/jarredou/aufr33_MelBand_Denoise/resolve/main/denoise_mel_band_roformer_aufr33_aggr_sdr_27.9768.ckpt",
    },
    {
        "name": "UVR Denoise",
        "full_name": "UVR-DeNoise.pth",
        "arch": "vr",
    },
]

dereverb_models = [
    {
        "name": "MDX23C DeReverb by aufr33 and jarredou",
        "path": os.path.join(now_dir, "models", "mdx23c-dereveb"),
        "model": os.path.join(now_dir, "models", "mdx23c-dereveb", "model.ckpt"),
        "config": os.path.join(now_dir, "models", "mdx23c-dereveb", "config.yaml"),
        "type": "mdx23c",
        "config_url": "https://huggingface.co/jarredou/aufr33_jarredou_MDXv3_DeReverb/resolve/main/config_dereverb_mdx23c.yaml",
        "model_url": "https://huggingface.co/jarredou/aufr33_jarredou_MDXv3_DeReverb/resolve/main/dereverb_mdx23c_sdr_6.9096.ckpt",
    },
    {
        "name": "BS-Roformer Dereverb by anvuew",
        "path": os.path.join(now_dir, "models", "bs-dereverb"),
        "model": os.path.join(now_dir, "models", "bs-dereverb", "model.ckpt"),
        "config": os.path.join(now_dir, "models", "bs-dereverb", "config.yaml"),
        "type": "bs_roformer",
        "config_url": "https://huggingface.co/anvuew/deverb_bs_roformer/resolve/main/deverb_bs_roformer_8_384dim_10depth.yaml",
        "model_url": "https://huggingface.co/anvuew/deverb_bs_roformer/resolve/main/deverb_bs_roformer_8_384dim_10depth.ckpt",
    },
    {
        "name": "UVR-Deecho-Dereverb",
        "full_name": "UVR-DeEcho-DeReverb.pth",
        "arch": "vr",
    },
    {
        "name": "MDX Reverb HQ by FoxJoy",
        "full_name": "Reverb_HQ_By_FoxJoy.onnx",
        "arch": "mdx",
    },
]

# ===================================================================
# F0 Pitch Predictor Configuration
# ===================================================================
#
# All F0 predictor constants, model paths, download URLs, and default
# parameters are centralized here.  Predictor implementation files live
# under ``main/library/predictors/<METHOD>/<METHOD>.py`` and MUST import
# from this module instead of defining their own copies.
#
# The ``F0Generator`` class (Generator.py) lazy-loads predictors using
# the getter functions defined below.
#
# Getter functions follow the  ``get_<predictor>()``  pattern so that
# downstream code can obtain paths / values without hard-coding them.
# ===================================================================

# -- Base directories ------------------------------------------------
# Predictor models are stored here (downloaded by main/utils.py)
PREDICTORS_DIR = os.path.join(now_dir, "main", "rvc", "engine", "models", "predictors")
EMBEDDERS_DIR = os.path.join(now_dir, "main", "rvc", "engine", "models", "embedders")
# Predictor implementation source code lives here
PREDICTORS_LIB_DIR = os.path.join(now_dir, "main", "library", "predictors")

# -- Download source URLs ------------------------------------------------
PREDICTORS_URL_BASE = "https://huggingface.co/NeoPy/Ultimate-Models/resolve/main/predictors"
EMBEDDERS_URL_BASE = "https://huggingface.co/NeoPy/Ultimate-Models/resolve/main/embedders/transformers/contentvec_base"

# -- Public config dict used by Generator and other modules -------------
configs = {
    "predictors_path": PREDICTORS_DIR,
}

# -- CREPE / ONNX-CREPE constants (must match CREPE training) ---------
CREPE_CENTS_PER_BIN = 20
CREPE_MAX_FMAX = 2006.0
CREPE_PITCH_BINS = 360
CREPE_SAMPLE_RATE = 16000
CREPE_WINDOW_SIZE = 1024

# -- RMVPE constants -------------------------------------------------
RMVPE_N_MELS = 128
RMVPE_N_CLASS = 360
RMVPE_SAMPLE_RATE = 16000
RMVPE_WINDOW_SIZE = 1024
RMVPE_HOP_LENGTH = 160
RMVPE_MEL_FMIN = 30
RMVPE_MEL_FMAX = 8000

# -- FCPE constants --------------------------------------------------
FCPE_DEFAULT_THRESHOLD = 0.05

# -- Available F0 methods ---------------------------------------------
F0_METHODS = [
    "rmvpe",
    "crepe",
    "crepe-tiny",
    "fcpe",
    "onnxcrepe",
    "harvest",
    "mangio-crepe",
    "mangio-crepe-tiny",
    "fcpe-legacy",
    "hpa-rmvpe",
    "swipe",
    "penn",
    "mangio-penn",
    "djcm",
    "djcm-svs",
    "swift",
    "pesto",
    "hybrid[crepe+rmvpe]",
    "hybrid[crepe+fcpe]",
    "hybrid[rmvpe+fcpe]",
    "hybrid[rmvpe+hpa-rmvpe]",
    "hybrid[crepe+hpa-rmvpe]",
    "hybrid[rmvpe+penn]",
]
F0_METHODS_UI = [
    "rmvpe",
    "crepe",
    "crepe-tiny",
    "fcpe",
    "fcpe-legacy",
    "onnxcrepe",
    "harvest",
    "mangio-crepe",
    "mangio-crepe-tiny",
    "hpa-rmvpe",
    "swipe",
    "penn",
    "mangio-penn",
    "djcm",
    "djcm-svs",
    "swift",
    "pesto",
]
F0_HYBRID_PREFIX = "hybrid"

# -- F0 model file names ----------------------------------------------
F0_MODEL_FILES = {
    "rmvpe": "rmvpe.pt",
    "fcpe": "fcpe.pt",
    "fcpe-legacy": "fcpe_legacy.pt",
    "crepe": "crepe.onnx",
    "crepe-tiny": "crepe_tiny.onnx",
    "onnxcrepe": "crepe.onnx",
    "hpa-rmvpe": "hpa-rmvpe-112000.pt",
    "penn": "penn.onnx",
    "djcm": "djcm.pt",
    "djcm-svs": "djcm_svs.pt",
    "swift": "swift.onnx",
    "pesto": "pesto.onnx",
}

# -- F0 default parameters --------------------------------------------
F0_DEFAULTS = {
    "f0_min": 50,
    "f0_max": 1100,
    "sample_rate": 16000,
    "hop_length": 160,
    "crepe_hop_length": 160,
    "crepe_tiny_hop_length": 160,
    "crepe_f0_min": 50,
    "crepe_f0_max": 1100,
    "crepe_threshold": 0.03,
    "rmvpe_threshold": 0.03,
    "fcpe_threshold": 0.03,
}

# -- Predictor download manifest --------------------------------------
PREDICTOR_DOWNLOAD_FILES = [
    "rmvpe.pt",
    "fcpe.pt",
    "fcpe_legacy.pt",
    "crepe.onnx",
    "crepe_tiny.onnx",
    "hpa-rmvpe-112000.pt",
    "hpa-rmvpe-76000.pt",
    "penn.onnx",
    "djcm.pt",
    "djcm_svs.pt",
    "swift.onnx",
    "pesto.onnx",
]

# -- Download file lists -------------------------------------------------
predictors_list = [("predictors/", PREDICTOR_DOWNLOAD_FILES)]

embedders_list = [
    ("contentvec_base/", ["pytorch_model.bin", "config.json"]),
]

# -- Folder mapping (remote folder → local directory) --------------------
download_folder_mapping = {
    "predictors/": PREDICTORS_DIR,
    "contentvec_base/": os.path.join(EMBEDDERS_DIR, "contentvec"),
}



# ===================================================================
# Getter functions (only the ones actually used across the codebase)
# ===================================================================


def get_rmvpe_model_path() -> str:
    """Get the file path for the RMVPE predictor model."""
    return os.path.join(PREDICTORS_DIR, F0_MODEL_FILES["rmvpe"])


def get_fcpe_model_path() -> str:
    """Get the file path for the FCPE predictor model."""
    return os.path.join(PREDICTORS_DIR, F0_MODEL_FILES["fcpe"])


def get_crepe_model_path(model_size: str = "full") -> str:
    """Get the file path for the CREPE ONNX predictor model.

    Args:
        model_size: 'full' or 'tiny'
    """
    key = "crepe-tiny" if model_size == "tiny" else "crepe"
    return os.path.join(PREDICTORS_DIR, F0_MODEL_FILES[key])


def get_onnxcrepe_model_path(model_size: str = "full") -> str:
    """Get the file path for the ONNX CREPE predictor model.

    Args:
        model_size: 'full' or 'tiny'
    """
    key = "crepe-tiny" if model_size == "tiny" else "crepe"
    return os.path.join(PREDICTORS_DIR, F0_MODEL_FILES[key])


def get_predictors_dir() -> str:
    """Get the base directory for all predictor model files."""
    return PREDICTORS_DIR


def get_f0_defaults() -> dict:
    """Get default F0 extraction parameters."""
    return F0_DEFAULTS.copy()


def get_f0_methods_ui() -> list:
    """Get the list of F0 methods available in the UI dropdown."""
    return F0_METHODS_UI


deecho_models = [
    {
        "name": "UVR-Deecho-Normal",
        "full_name": "UVR-De-Echo-Normal.pth",
        "arch": "vr",
    },
    {
        "name": "UVR-Deecho-Agggressive",
        "full_name": "UVR-De-Echo-Aggressive.pth",
        "arch": "vr",
    },
]


# ===================================================================
# ACE-Step Music Generation Configuration
# ===================================================================
#
# All ACE-Step constants, model choices, output paths, and UI defaults
# are centralized here.  The tab module (tabs/acestep_tab.py) and the
# inference backend (main/acestep_inference.py) MUST import from this
# module instead of defining their own copies.
#
# Getter functions follow the ``get_<name>()``  pattern so that
# downstream code can obtain values without hard-coding them.
# ===================================================================

# -- Output directory ------------------------------------------------
ACESTEP_OUTPUT_DIR = os.path.join(now_dir, "audio_files", "acestep_output")

# -- Valid vocal languages for music generation ----------------------
ACESTEP_VALID_LANGUAGES = [
    "unknown", "en", "zh", "ja", "ko", "es", "fr", "de", "it", "pt",
    "ru", "ar", "hi", "th", "vi", "id", "tr", "nl", "pl", "uk",
    "bn", "fa", "he", "sv", "da", "fi", "no", "cs", "el", "ro",
    "hu", "sk", "bg", "hr", "ca", "fil", "ms", "ta", "te", "ur",
]

# -- Supported audio output formats ----------------------------------
ACESTEP_AUDIO_FORMATS = ["flac", "wav", "mp3"]

# -- DiT (audio generator) model choices ----------------------------
ACESTEP_DIT_MODEL_CHOICES = [
    "acestep-v15-turbo",
    "acestep-v15-sft",
    "acestep-v15-base",
    "acestep-v15-xl-turbo",
    "acestep-v15-xl-sft",
    "acestep-v15-xl-base",
]

# -- LM (reasoning planner) model choices ----------------------------
ACESTEP_LM_MODEL_CHOICES = [
    "acestep-5Hz-lm-0.6B",
    "acestep-5Hz-lm-1.7B",
    "acestep-5Hz-lm-4B",
]

# -- Time signature mapping (UI label -> internal value) ------------
ACESTEP_TIME_SIGNATURE_MAP = {
    "Auto": "",
    "2/4": "2",
    "3/4": "3",
    "4/4": "4",
    "6/8": "6",
}

# -- Generation task modes -------------------------------------------
ACESTEP_TASK_MODES = ["Simple", "Custom", "Cover", "Repaint"]

# -- HuggingFace model links -----------------------------------------
ACESTEP_HF_ORG = "ACE-Step"
ACESTEP_HF_REPO = "Ace-Step1.5"
ACESTEP_HF_MODELS = {
    "acestep-v15-turbo": "https://huggingface.co/ACE-Step/acestep-v15-turbo",
    "acestep-v15-sft": "https://huggingface.co/ACE-Step/acestep-v15-sft",
    "acestep-v15-base": "https://huggingface.co/ACE-Step/acestep-v15-base",
    "acestep-v15-xl-turbo": "https://huggingface.co/ACE-Step/acestep-v15-xl-turbo",
    "acestep-v15-xl-sft": "https://huggingface.co/ACE-Step/acestep-v15-xl-sft",
    "acestep-v15-xl-base": "https://huggingface.co/ACE-Step/acestep-v15-xl-base",
}
ACESTEP_GITHUB_REPO = "https://github.com/ACE-Step/ACE-Step-1.5"

# -- Inference defaults ----------------------------------------------
ACESTEP_DEFAULTS = {
    "dit_model": "acestep-v15-turbo",
    "lm_model": "acestep-5Hz-lm-0.6B",
    "lm_backend": "vllm",
    "use_lm": True,
    "device": "auto",
    "inference_steps": 8,
    "guidance_scale": 7.0,
    "seed": -1,
    "batch_size": 2,
    "duration": 30,
    "lm_temperature": 0.85,
    "audio_format": "flac",
    "vocal_language": "en",
    "thinking": True,
}


# -- Getter functions ------------------------------------------------

def get_acestep_output_dir() -> str:
    """Get the output directory for ACE-Step generated music."""
    return ACESTEP_OUTPUT_DIR


def get_acestep_valid_languages() -> list:
    """Get the list of supported vocal languages."""
    return list(ACESTEP_VALID_LANGUAGES)


def get_acestep_audio_formats() -> list:
    """Get the list of supported output audio formats."""
    return list(ACESTEP_AUDIO_FORMATS)


def get_acestep_dit_model_choices() -> list:
    """Get the list of available DiT model names."""
    return list(ACESTEP_DIT_MODEL_CHOICES)


def get_acestep_lm_model_choices() -> list:
    """Get the list of available LM model names."""
    return list(ACESTEP_LM_MODEL_CHOICES)


def get_acestep_time_signature_map() -> dict:
    """Get the time signature UI-label-to-internal mapping."""
    return dict(ACESTEP_TIME_SIGNATURE_MAP)


def get_acestep_task_modes() -> list:
    """Get the list of generation task mode labels."""
    return list(ACESTEP_TASK_MODES)


def get_acestep_hf_models() -> dict:
    """Get the HuggingFace model URL mapping."""
    return dict(ACESTEP_HF_MODELS)


def get_acestep_defaults() -> dict:
    """Get the default ACE-Step inference parameters."""
    return ACESTEP_DEFAULTS.copy()
