"""
Text-to-Speech synthesis module for Hyper-RVC.

Provides:
- Edge TTS integration (async + sync wrappers)
- Complete TTS → RVC pipeline
- Voice / language / rate option discovery
"""

import os
import sys
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import edge_tts

now_dir = os.getcwd()
sys.path.append(now_dir)

from main.tools.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Voice catalogues
# ---------------------------------------------------------------------------

EDGE_TTS_VOICES: Dict[str, List[str]] = {
    # English
    "English (US)": [
        "en-US-JennyNeural", "en-US-GuyNeural", "en-US-AriaNeural", "en-US-DavisNeural",
        "en-US-AmberNeural", "en-US-AnaNeural", "en-US-AshleyNeural", "en-US-BrandonNeural",
        "en-US-ChristopherNeural", "en-US-CoraNeural", "en-US-ElizabethNeural", "en-US-EricNeural",
        "en-US-JacobNeural", "en-US-MichelleNeural", "en-US-MonicaNeural", "en-US-RogerNeural",
    ],
    "English (UK)": [
        "en-GB-SoniaNeural", "en-GB-RyanNeural", "en-GB-LibbyNeural", "en-GB-AbbiNeural",
        "en-GB-AlfieNeural", "en-GB-BellaNeural", "en-GB-ElliotNeural", "en-GB-EthanNeural",
        "en-GB-HollieNeural", "en-GB-MaisieNeural", "en-GB-NoahNeural", "en-GB-OliverNeural",
        "en-GB-OliviaNeural", "en-GB-ThomasNeural",
    ],
    "English (Australia)": [
        "en-AU-NatashaNeural", "en-AU-WilliamNeural", "en-AU-AnnetteNeural", "en-AU-CarlyNeural",
        "en-AU-DarrenNeural", "en-AU-DuncanNeural", "en-AU-ElsieNeural", "en-AU-FreyaNeural",
        "en-AU-JoanneNeural", "en-AU-KimNeural", "en-AU-MeganNeural", "en-AU-RebeccaNeural",
        "en-AU-TimNeural",
    ],
    "English (Canada)": [
        "en-CA-ClaraNeural", "en-CA-LiamNeural",
    ],
    "English (India)": [
        "en-IN-NeerjaNeural", "en-IN-PrabhatNeural",
    ],
    # Spanish
    "Spanish (Spain)": [
        "es-ES-ElviraNeural", "es-ES-AlvaroNeural",
    ],
    "Spanish (Mexico)": [
        "es-MX-DaliaNeural", "es-MX-JorgeNeural",
    ],
    "Spanish (Argentina)": [
        "es-AR-ElenaNeural", "es-AR-TomasNeural",
    ],
    "Spanish (Colombia)": [
        "es-CO-SalomeNeural", "es-CO-GonzaloNeural",
    ],
    # French
    "French (France)": [
        "fr-FR-DeniseNeural", "fr-FR-HenriNeural",
    ],
    "French (Canada)": [
        "fr-CA-SylvieNeural", "fr-CA-JeanNeural", "fr-CA-AntoineNeural",
    ],
    # German
    "German": [
        "de-DE-KatjaNeural", "de-DE-ConradNeural", "de-DE-AmalaNeural", "de-DE-BerndNeural",
        "de-DE-ChristophNeural", "de-DE-ElkeNeural", "de-DE-GiselaNeural", "de-DE-KasperNeural",
        "de-DE-KillianNeural", "de-DE-KlarissaNeural", "de-DE-KlausNeural", "de-DE-LouisaNeural",
        "de-DE-MajaNeural", "de-DE-RalfNeural", "de-DE-TanjaNeural",
    ],
    # Portuguese
    "Portuguese (Brazil)": [
        "pt-BR-FranciscaNeural", "pt-BR-AntonioNeural", "pt-BR-BrendaNeural", "pt-BR-DonatoNeural",
        "pt-BR-ElzaNeural", "pt-BR-FabioNeural", "pt-BR-GiovannaNeural", "pt-BR-HumbertoNeural",
        "pt-BR-JulioNeural", "pt-BR-LeilaNeural", "pt-BR-LeticiaNeural", "pt-BR-ManuelaNeural",
        "pt-BR-NicolauNeural", "pt-BR-ValerioNeural", "pt-BR-YaraNeural",
    ],
    "Portuguese (Portugal)": [
        "pt-PT-RaquelNeural", "pt-PT-DuarteNeural",
    ],
    # Italian
    "Italian": [
        "it-IT-ElsaNeural", "it-IT-DiegoNeural", "it-IT-BenignoNeural", "it-IT-CalimeroNeural",
        "it-IT-CataldoNeural", "it-IT-FabiolaNeural", "it-IT-FiammaNeural", "it-IT-GianniNeural",
        "it-IT-ImmaNeural", "it-IT-IrmaNeural", "it-IT-LisandroNeural", "it-IT-PalmiraNeural",
        "it-IT-PierinaNeural", "it-IT-RinaldoNeural",
    ],
    # Japanese
    "Japanese": [
        "ja-JP-NanamiNeural", "ja-JP-KeitaNeural", "ja-JP-AoiNeural", "ja-JP-DaichiNeural",
        "ja-JP-MayuNeural", "ja-JP-NaokiNeural", "ja-JP-ShioriNeural",
    ],
    # Korean
    "Korean": [
        "ko-KR-SunHiNeural", "ko-KR-InJoonNeural", "ko-KR-BongJinNeural", "ko-KR-GookMinNeural",
        "ko-KR-JiMinNeural", "ko-KR-SeoHyeonNeural", "ko-KR-SoonBokNeural", "ko-KR-YuJinNeural",
    ],
    # Chinese
    "Chinese (Mandarin)": [
        "zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural", "zh-CN-YunyangNeural", "zh-CN-XiaoyiNeural",
        "zh-CN-YunjianNeural", "zh-CN-XiaochenNeural", "zh-CN-XiaohanNeural", "zh-CN-XiaomengNeural",
        "zh-CN-XiaomoNeural", "zh-CN-XiaoqiuNeural", "zh-CN-XiaoruiNeural", "zh-CN-XiaoshuangNeural",
        "zh-CN-XiaoxuanNeural", "zh-CN-XiaoyanNeural", "zh-CN-XiaoyouNeural", "zh-CN-XiaozhenNeural",
        "zh-CN-YunfengNeural", "zh-CN-YunhaoNeural", "zh-CN-YunxiaNeural", "zh-CN-YunyeNeural", "zh-CN-YunzeNeural",
    ],
    "Chinese (Cantonese)": [
        "zh-HK-HiuGaaiNeural", "zh-HK-WanLungNeural", "zh-HK-SiuLamNeural",
    ],
    "Chinese (Taiwan)": [
        "zh-TW-HsiaoChenNeural", "zh-TW-YunJheNeural",
    ],
    # Russian
    "Russian": ["ru-RU-SvetlanaNeural", "ru-RU-DmitryNeural"],
    # Arabic
    "Arabic": ["ar-SA-ZariyahNeural", "ar-SA-HamedNeural"],
    # Hindi
    "Hindi": ["hi-IN-SwaraNeural", "hi-IN-MadhurNeural"],
    # Dutch
    "Dutch": [
        "nl-NL-ColetteNeural", "nl-NL-FennaNeural", "nl-NL-MaartenNeural",
    ],
    # Polish
    "Polish": [
        "pl-PL-AgnieszkaNeural", "pl-PL-MarekNeural", "pl-PL-ZofiaNeural",
    ],
    # Turkish
    "Turkish": [
        "tr-TR-AhmetNeural", "tr-TR-EmelNeural",
    ],
    # Swedish
    "Swedish": [
        "sv-SE-SofieNeural", "sv-SE-MattiasNeural",
    ],
    # Danish
    "Danish": [
        "da-DK-ChristelNeural", "da-DK-JeppeNeural",
    ],
    # Finnish
    "Finnish": [
        "fi-FI-NooraNeural", "fi-FI-HarriNeural",
    ],
    # Norwegian
    "Norwegian": [
        "no-NO-PernilleNeural", "no-NO-FinnNeural",
    ],
    # Ukrainian
    "Ukrainian": ["uk-UA-PolinaNeural", "uk-UA-OstapNeural"],
    # Romanian
    "Romanian": ["ro-RO-AlinaNeural", "ro-RO-EmilNeural"],
    # Hungarian
    "Hungarian": ["hu-HU-NoemiNeural", "hu-HU-TamasNeural"],
    # Czech
    "Czech": ["cs-CZ-AntoninNeural", "cs-CZ-VlastaNeural"],
    # Greek
    "Greek": ["el-GR-AthinaNeural", "el-GR-NestorasNeural"],
    # Hebrew
    "Hebrew": ["he-IL-HilaNeural", "he-IL-AvriNeural"],
    # Thai
    "Thai": ["th-TH-PremwadeeNeural", "th-TH-NiwatNeural"],
    # Vietnamese
    "Vietnamese": ["vi-VN-HoaiMyNeural", "vi-VN-NamMinhNeural"],
    # Indonesian
    "Indonesian": ["id-ID-GadisNeural", "id-ID-ArdiNeural"],
    # Malay
    "Malay": ["ms-MY-YasminNeural", "ms-MY-OsmanNeural"],
    # Catalan
    "Catalan": ["ca-ES-JoanaNeural", "ca-ES-EnricNeural"],
    # Bulgarian
    "Bulgarian": ["bg-BG-KalinaNeural", "bg-BG-BorislavNeural"],
    # Croatian
    "Croatian": ["hr-HR-GabrijelaNeural", "hr-HR-SreckoNeural"],
    # Slovak
    "Slovak": ["sk-SK-LukasNeural", "sk-SK-ViktoriaNeural"],
    # Slovenian
    "Slovenian": ["sl-SI-PetraNeural", "sl-SI-RokNeural"],
    # Estonian
    "Estonian": ["et-EE-KertNeural", "et-EE-AnuNeural"],
    # Lithuanian
    "Lithuanian": ["lt-LT-LeonasNeural", "lt-LT-OnaNeural"],
    # Latvian
    "Latvian": ["lv-LV-EveritaNeural", "lv-LV-NilsNeural"],
    # Basque
    "Basque": ["eu-ES-AinhoaNeural", "eu-ES-AitorNeural"],
    # Galician
    "Galician": ["gl-ES-SabelaNeural", "gl-ES-RoiNeural"],
    # Welsh
    "Welsh": ["cy-GB-NiaNeural", "cy-GB-AledNeural"],
    # Bengali
    "Bengali": ["bn-BD-NabanitaNeural", "bn-BD-PradeepNeural"],
    # Tamil
    "Tamil": ["ta-IN-PallaviNeural", "ta-IN-ValluvarNeural"],
    # Telugu
    "Telugu": ["te-IN-ShrutiNeural", "te-IN-MohanNeural"],
    # Malayalam
    "Malayalam": ["ml-IN-SobhanaNeural", "ml-IN-MidhunNeural"],
    # Kannada
    "Kannada": ["kn-IN-SapthaNeural", "kn-IN-GaganNeural"],
    # Urdu
    "Urdu": ["ur-PK-UzmaNeural", "ur-PK-SalmanNeural"],
    # Persian
    "Persian": ["fa-IR-DilaraNeural", "fa-IR-FaridNeural"],
    # Swahili
    "Swahili": ["sw-KE-ZuriNeural", "sw-KE-YusufNeural"],
    # Filipino
    "Filipino": ["fil-PH-AngelaNeural", "fil-PH-BuenoNeural"],
    # Serbian
    "Serbian": ["sr-RS-NicholasNeural", "sr-RS-SophieNeural"],
    # Indonesian (Javanese) 
    "Javanese": ["jv-ID-SitiNeural", "jv-ID-DimasNeural"],
}


# ---------------------------------------------------------------------------
# Rate options
# ---------------------------------------------------------------------------

TTS_RATE_OPTIONS: Dict[str, int] = {
    "Very Slow (-30%)": -30,
    "Slow (-20%)": -20,
    "Slightly Slow (-10%)": -10,
    "Normal (0%)": 0,
    "Slightly Fast (+10%)": 10,
    "Fast (+20%)": 20,
    "Very Fast (+30%)": 30,
}


# ---------------------------------------------------------------------------
# Internal async helper
# ---------------------------------------------------------------------------

async def _run_edge_tts_async(
    text: str,
    voice: str,
    rate: int,
    output_path: str,
) -> Tuple[bool, str]:
    """
    Internal async function to run Edge TTS.

    Args:
        text: Text to synthesize.
        voice: Voice ID to use.
        rate: Speech rate percentage.
        output_path: Path to save the output audio file.

    Returns:
        Tuple of (success, message).
    """
    try:
        rate_str = f"+{rate}%" if rate >= 0 else f"{rate}%"
        communicate = edge_tts.Communicate(text, voice, rate=rate_str)
        await communicate.save(output_path)
        return True, f"TTS generated successfully with voice: {voice}"
    except Exception as e:
        return False, f"TTS generation failed: {str(e)}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_edge_tts(
    text: str,
    voice: str,
    rate: int,
    output_path: str,
) -> Tuple[bool, str]:
    """
    Run Edge TTS to generate speech from text (blocking wrapper).

    Args:
        text: Text to convert to speech.
        voice: Voice ID to use.
        rate: Speech rate percentage (e.g. ``0`` for normal).
        output_path: Path to save the output audio file.

    Returns:
        Tuple of (success, message).
    """
    return asyncio.run(_run_edge_tts_async(text, voice, rate, output_path))


def run_tts_inference(
    text: str,
    language: str,
    voice: str,
    rate: int,
    use_rvc: bool,
    model_path: str,
    index_path: str,
    pitch: int,
    pitch_extract: str,
    filter_radius: int,
    index_rate: float,
    rms_mix_rate: float,
    protect: float,
    embedder_model: str,
    devices: str,
    export_format: str,
) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Run the complete TTS inference pipeline.

    1. Generate speech via Edge TTS.
    2. Optionally apply RVC voice conversion.

    Args:
        text:          Text to synthesize.
        language:      Language category (unused directly; voice already
                       encodes the locale).
        voice:         Edge TTS voice ID.
        rate:          Speech rate percentage.
        use_rvc:       Whether to apply RVC voice conversion after TTS.
        model_path:    Path to the RVC model file.
        index_path:    Path to the RVC index file.
        pitch:         Pitch adjustment in semitones.
        pitch_extract: Pitch extraction method for RVC.
        filter_radius: Median filter radius for RVC.
        index_rate:    Feature search ratio for RVC.
        rms_mix_rate:  Volume envelope mix rate for RVC.
        protect:       Breath protection for RVC.
        embedder_model: Embedder model for RVC.
        devices:       Device selection (e.g. ``"0"`` or ``"cpu"``).
        export_format: Export format (e.g. ``"WAV"``, ``"MP3"``).

    Returns:
        Tuple of ``(status_message, tts_audio_path, final_audio_path)``.
        *final_audio_path* is ``None`` when RVC is not used.
    """
    # Validate input
    if not text or not text.strip():
        return "Error: Text is empty", None, None

    if len(text) > 5000:
        return "Error: Text too long (max 5000 characters)", None, None

    # Create output directory
    output_dir = os.path.join(now_dir, "audio_files", "tts_output")
    os.makedirs(output_dir, exist_ok=True)

    # Generate filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tts_output_path = os.path.join(output_dir, f"tts_{timestamp}.wav")
    rvc_output_path = os.path.join(
        output_dir, f"tts_rvc_{timestamp}.{export_format.lower()}"
    )

    # Step 1: Generate TTS
    success, tts_message = run_edge_tts(text, voice, rate, tts_output_path)

    if not success:
        return tts_message, None, None

    # If RVC not enabled, return TTS output
    if not use_rvc:
        return f"TTS completed: {voice}", tts_output_path, None

    # Step 2: Apply RVC voice conversion
    if not model_path or not os.path.exists(model_path):
        return "RVC model not found", tts_output_path, None

    # Deferred import to avoid circular dependency
    from main.rvc.converter import run_rvc_conversion

    rvc_output = os.path.join(output_dir, f"tts_rvc_{timestamp}.{export_format.lower()}")

    try:
        run_rvc_conversion(
            audio_input_path=tts_output_path,
            audio_output_path=rvc_output,
            model_path=model_path,
            index_path=index_path,
            embedder_model=embedder_model,
            pitch=pitch,
            f0_method=pitch_extract,
            filter_radius=filter_radius,
            index_rate=index_rate,
            volume_envelope=rms_mix_rate,
            protect=protect,
            split_audio=False,
            f0_autotune=False,
            hop_length=64,
            export_format=export_format,
        )
        return f"TTS + RVC completed: {voice}", tts_output_path, rvc_output
    except Exception as e:
        logger.error(f"RVC conversion error in TTS pipeline: {e}")
        return f"RVC conversion failed: {str(e)}", tts_output_path, None


# ---------------------------------------------------------------------------
# Option discovery helpers
# ---------------------------------------------------------------------------

def get_tts_voices(language: str) -> list:
    """
    Get list of available TTS voices for a language.

    Args:
        language: Language category key from ``EDGE_TTS_VOICES``.

    Returns:
        List of voice ID strings. Falls back to English (US) if the
        language is not found.
    """
    return EDGE_TTS_VOICES.get(language, EDGE_TTS_VOICES["English (US)"])


def get_tts_languages() -> list:
    """
    Get list of available TTS language categories.

    Returns:
        List of language name strings.
    """
    return list(EDGE_TTS_VOICES.keys())


def get_tts_rate_options() -> dict:
    """
    Get dictionary of TTS rate options.

    Returns:
        Dictionary mapping rate display names to integer percentage values.
    """
    return TTS_RATE_OPTIONS
