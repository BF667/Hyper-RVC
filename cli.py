#!/usr/bin/env python3
"""
CLI for audio processing with vocal separation, RVC conversion, and audio effects.

Hyper RVC CLI provides command-line access to the full audio processing pipeline,
including vocal separation, voice conversion, and audio effects.
"""

import argparse
import os
import sys
from pathlib import Path

# Add the current directory to path to import main
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import core  # core.py is now a backward-compat shim that re-exports from main


# Supported audio formats
SUPPORTED_AUDIO_FORMATS = {
    '.wav', '.mp3', '.flac', '.ogg', '.opus', '.m4a', '.aac', '.wma'
}


def validate_file_exists(path: str, file_type: str) -> str:
    """
    Validate that a file exists.
    
    Args:
        path: Path to the file
        file_type: Description of the file type for error messages
        
    Returns:
        Validated path
        
    Raises:
        argparse.ArgumentTypeError: If file doesn't exist
    """
    if not os.path.exists(path):
        raise argparse.ArgumentTypeError(
            f"{file_type} file does not exist: {path}"
        )
    return path


def validate_audio_file(path: str) -> str:
    """
    Validate that a file is a supported audio format.
    
    Args:
        path: Path to the audio file
        
    Returns:
        Validated path
        
    Raises:
        argparse.ArgumentTypeError: If file is not a supported audio format
    """
    path = validate_file_exists(path, "Audio")
    ext = Path(path).suffix.lower()
    if ext not in SUPPORTED_AUDIO_FORMATS:
        raise argparse.ArgumentTypeError(
            f"Unsupported audio format '{ext}'. Supported formats: {', '.join(sorted(SUPPORTED_AUDIO_FORMATS))}"
        )
    return path


def validate_positive_int(value: str) -> int:
    """
    Validate that a value is a positive integer.
    
    Args:
        value: String value to validate
        
    Returns:
        Validated integer
        
    Raises:
        argparse.ArgumentTypeError: If value is not a positive integer
    """
    try:
        ivalue = int(value)
        if ivalue <= 0:
            raise argparse.ArgumentTypeError(
                f"Value must be a positive integer, got {ivalue}"
            )
        return ivalue
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid integer value: {value}"
        )


def validate_float_range(value: str, min_val: float, max_val: float, name: str) -> float:
    """
    Validate that a value is a float within a specified range.
    
    Args:
        value: String value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        name: Name of the parameter for error messages
        
    Returns:
        Validated float
        
    Raises:
        argparse.ArgumentTypeError: If value is out of range
    """
    try:
        fvalue = float(value)
        if fvalue < min_val or fvalue > max_val:
            raise argparse.ArgumentTypeError(
                f"{name} must be between {min_val} and {max_val}, got {fvalue}"
            )
        return fvalue
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid float value for {name}: {value}"
        )


def list_models(args):
    """List all available models"""
    print("\n" + "=" * 60)
    print("HYPER-RVC AVAILABLE MODELS")
    print("=" * 60)
    
    print("\n🎤 VOCALS SEPARATION MODELS")
    print("-" * 40)
    for idx, model in enumerate(core.models_vocals, 1):
        print(f"  {idx}. {model['name']}")

    print("\n🎵 KARAOKE MODELS")
    print("-" * 40)
    for idx, model in enumerate(core.karaoke_models, 1):
        print(f"  {idx}. {model['name']}")

    print("\n✨ DEREVERB MODELS")
    print("-" * 40)
    for idx, model in enumerate(core.dereverb_models, 1):
        print(f"  {idx}. {model['name']}")

    print("\n🔊 DEECHO MODELS")
    print("-" * 40)
    for idx, model in enumerate(core.deecho_models, 1):
        print(f"  {idx}. {model['name']}")

    print("\n🧹 DENOISE MODELS")
    print("-" * 40)
    for idx, model in enumerate(core.denoise_models, 1):
        print(f"  {idx}. {model['name']}")
    
    print("\n" + "=" * 60)
    print(f"Total: {sum([len(core.models_vocals), len(core.karaoke_models), len(core.dereverb_models), len(core.deecho_models), len(core.denoise_models)])} models available")
    print("=" * 60 + "\n")


def show_config(args):
    """Show current configuration"""
    from main.tools.config import get_config
    
    config = get_config()
    
    print("\n" + "=" * 60)
    print("HYPER-RVC CONFIGURATION")
    print("=" * 60)
    
    print(f"\n📁 Config file: {config.config_path}")
    print(f"   Exists: {os.path.exists(config.config_path)}")
    
    print("\n🎵 Audio Settings")
    print("-" * 40)
    audio = config.audio
    for key, value in audio.items():
        print(f"   {key}: {value}")
    
    print("\n🤖 Model Defaults")
    print("-" * 40)
    models = config.models
    for key, value in models.items():
        print(f"   {key}: {value}")
    
    print("\n💻 Hardware Settings")
    print("-" * 40)
    hardware = config.hardware
    for key, value in hardware.items():
        print(f"   {key}: {value}")
    
    print("\n🎨 UI Settings")
    print("-" * 40)
    ui = config.ui
    for key, value in ui.items():
        print(f"   {key}: {value}")
    
    print("\n" + "=" * 60 + "\n")


def download_model(args):
    """Download a model"""
    result = core.download_model(args.link)
    print(result)


def download_music(args):
    """Download music from a link"""
    result = core.download_music(args.link)
    print(result)


def convert_audio(args):
    """Main audio conversion pipeline"""
    import logging
    from main.tools.logger import get_logger
    
    logger = get_logger(__name__)
    
    logger.info("Starting audio conversion pipeline...")

    # Validate model files exist
    if not os.path.exists(args.model_path):
        logger.error(f"Model path '{args.model_path}' does not exist")
        print(f"❌ Error: Model path '{args.model_path}' does not exist")
        return 1

    if args.index_path and not os.path.exists(args.index_path):
        logger.error(f"Index path '{args.index_path}' does not exist")
        print(f"❌ Error: Index path '{args.index_path}' does not exist")
        return 1

    if not os.path.exists(args.input_audio):
        logger.error(f"Input audio '{args.input_audio}' does not exist")
        print(f"❌ Error: Input audio '{args.input_audio}' does not exist")
        return 1

    # Validate audio format
    input_ext = Path(args.input_audio).suffix.lower()
    if input_ext not in SUPPORTED_AUDIO_FORMATS:
        logger.error(f"Unsupported audio format: {input_ext}")
        print(f"❌ Error: Unsupported audio format '{input_ext}'")
        print(f"   Supported formats: {', '.join(sorted(SUPPORTED_AUDIO_FORMATS))}")
        return 1

    logger.info(f"Input audio: {args.input_audio}")
    logger.info(f"Model: {args.model_path}")
    if args.index_path:
        logger.info(f"Index: {args.index_path}")

    # Prepare parameters with defaults
    params = {
        'model_path': args.model_path,
        'index_path': args.index_path,
        'input_audio_path': args.input_audio,
        'output_path': args.output_path or os.path.dirname(args.input_audio),
        'export_format_rvc': args.export_format_rvc,
        'split_audio': args.split_audio,
        'autotune': args.autotune,
        'vocal_model': args.vocal_model,
        'karaoke_model': args.karaoke_model,
        'dereverb_model': args.dereverb_model,
        'deecho': args.deecho,
        'deecho_model': args.deecho_model,
        'denoise': args.denoise,
        'denoise_model': args.denoise_model,
        'reverb': args.reverb,
        'vocals_volume': args.vocals_volume,
        'instrumentals_volume': args.instrumentals_volume,
        'backing_vocals_volume': args.backing_vocals_volume,
        'export_format_final': args.export_format_final,
        'devices': args.devices,
        'pitch': args.pitch,
        'filter_radius': args.filter_radius,
        'index_rate': args.index_rate,
        'rms_mix_rate': args.rms_mix_rate,
        'protect': args.protect,
        'pitch_extract': args.pitch_extract,
        'hop_lenght': args.hop_length,
        'reverb_room_size': args.reverb_room_size,
        'reverb_damping': args.reverb_damping,
        'reverb_wet_gain': args.reverb_wet_gain,
        'reverb_dry_gain': args.reverb_dry_gain,
        'reverb_width': args.reverb_width,
        'embedder_model': args.embedder_model,
        'delete_audios': args.delete_audios,
        'use_tta': args.use_tta,
        'batch_size': args.batch_size,
        'infer_backing_vocals': args.infer_backing_vocals,
        'infer_backing_vocals_model': args.infer_backing_vocals_model,
        'infer_backing_vocals_index': args.infer_backing_vocals_index,
        'change_inst_pitch': args.change_inst_pitch,
        'pitch_back': args.pitch_back,
        'filter_radius_back': args.filter_radius_back,
        'index_rate_back': args.index_rate_back,
        'rms_mix_rate_back': args.rms_mix_rate_back,
        'protect_back': args.protect_back,
        'pitch_extract_back': args.pitch_extract_back,
        'hop_length_back': args.hop_length_back,
        'export_format_rvc_back': args.export_format_rvc_back,
        'split_audio_back': args.split_audio_back,
        'autotune_back': args.autotune_back,
        'embedder_model_back': args.embedder_model_back,
    }

    # Run the full inference program
    try:
        logger.info("Running inference pipeline...")
        message, output_file = core.full_inference_program(**params)
        print(f"\n✅ {message}")
        print(f"📁 Output saved to: {output_file}")
        logger.info(f"Conversion completed successfully: {output_file}")
        return 0
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        print(f"\n❌ File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error during conversion: {e}", exc_info=True)
        print(f"\n❌ Error during conversion: {e}")
        return 1


def add_effects(args):
    """Add reverb effects to an audio file"""
    if not os.path.exists(args.input_audio):
        print(f"Error: Input audio '{args.input_audio}' does not exist")
        return 1
    
    output_path = args.output_path or args.input_audio.replace('.', '_with_reverb.')
    
    result = core.add_audio_effects(
        audio_path=args.input_audio,
        reverb_size=args.room_size,
        reverb_wet=args.wet,
        reverb_dry=args.dry,
        reverb_damping=args.damping,
        reverb_width=args.width,
        output_path=output_path
    )
    
    print(f"✅ Reverb effects added successfully")
    print(f"📁 Output saved to: {result}")
    return 0


def merge_audio(args):
    """Merge multiple audio files"""
    if not os.path.exists(args.vocals):
        print(f"Error: Vocals file '{args.vocals}' does not exist")
        return 1
    
    if not os.path.exists(args.instrumental):
        print(f"Error: Instrumental file '{args.instrumental}' does not exist")
        return 1
    
    if not os.path.exists(args.backing_vocals):
        print(f"Error: Backing vocals file '{args.backing_vocals}' does not exist")
        return 1
    
    output_path = args.output_path or "merged_audio." + args.format.lower()
    
    result = core.merge_audios(
        vocals_path=args.vocals,
        inst_path=args.instrumental,
        backing_path=args.backing_vocals,
        output_path=output_path,
        main_gain=args.vocals_gain,
        inst_gain=args.instrumental_gain,
        backing_Vol=args.backing_gain,
        output_format=args.format
    )
    
    print(f"✅ Audio files merged successfully")
    print(f"📁 Output saved to: {result}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Hyper RVC CLI - Audio processing with vocal separation and RVC voice conversion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all available models
  python cli.py list-models

  # Show current configuration
  python cli.py show-config

  # Download a model
  python cli.py download-model --link https://huggingface.co/model

  # Download music from YouTube
  python cli.py download-music --link https://youtube.com/watch?v=...

  # Convert audio with default settings
  python cli.py convert --model-path /path/to/model.pth --input-audio song.mp3

  # Full conversion with all options
  python cli.py convert --model-path model.pth --index-path index.pth \\
    --input-audio song.mp3 --pitch 12 --reverb --denoise \\
    --vocal-model "Mel-Roformer by KimberleyJSN" \\
    --export-format-final mp3

  # Add reverb to an audio file
  python cli.py add-effects input.wav --room-size 0.5 --wet 0.3

  # Merge audio files
  python cli.py merge --vocals vocals.flac --instrumental inst.flac \\
    --backing-vocals backing.flac --format mp3

For more information, visit: https://github.com/BF667-IDLE/Hyper-RVC
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # List models command
    parser_list = subparsers.add_parser('list-models', help='List all available models')
    parser_list.set_defaults(func=list_models)

    # Show config command
    parser_config = subparsers.add_parser('show-config', help='Show current configuration')
    parser_config.set_defaults(func=show_config)

    # Download model command
    parser_download_model = subparsers.add_parser('download-model', help='Download a model')
    parser_download_model.add_argument('--link', required=True, help='Link to download the model')
    parser_download_model.set_defaults(func=download_model)
    
    # Download music command
    parser_download_music = subparsers.add_parser('download-music', help='Download music from a link (YouTube, etc.)')
    parser_download_music.add_argument('--link', required=True, help='Link to download music from')
    parser_download_music.set_defaults(func=download_music)
    
    # Convert audio command (main pipeline)
    parser_convert = subparsers.add_parser('convert', help='Run the full audio conversion pipeline')
    
    # Required arguments
    parser_convert.add_argument('--model-path', required=True, help='Path to the RVC model')
    parser_convert.add_argument('--input-audio', required=True, help='Path to input audio file')
    
    # Optional arguments with defaults
    parser_convert.add_argument('--index-path', help='Path to index file (optional)')
    parser_convert.add_argument('--output-path', help='Output directory path')
    parser_convert.add_argument('--export-format-rvc', default='wav', choices=['wav', 'flac', 'mp3'], 
                               help='Export format for RVC output')
    parser_convert.add_argument('--split-audio', action='store_true', help='Split audio for processing')
    parser_convert.add_argument('--autotune', action='store_true', help='Apply autotune')
    
    # Model selection
    parser_convert.add_argument('--vocal-model', default='Mel-Roformer by KimberleyJSN', 
                               help='Vocal separation model to use')
    parser_convert.add_argument('--karaoke-model', default='Mel-Roformer Karaoke by aufr33 and viperx', 
                               help='Karaoke separation model to use')
    parser_convert.add_argument('--dereverb-model', default='MDX23C DeReverb by aufr33 and jarredou', 
                               help='Dereverb model to use')
    parser_convert.add_argument('--deecho-model', default='UVR-Deecho-Normal', 
                               help='Deecho model to use')
    parser_convert.add_argument('--denoise-model', default='Mel-Roformer Denoise Normal by aufr33', 
                               help='Denoise model to use')
    
    # Processing options
    parser_convert.add_argument('--deecho', action='store_true', help='Apply deecho processing')
    parser_convert.add_argument('--denoise', action='store_true', help='Apply denoise processing')
    parser_convert.add_argument('--reverb', action='store_true', help='Apply reverb effect')
    parser_convert.add_argument('--delete-audios', action='store_true', 
                               help='Delete intermediate audio files')
    parser_convert.add_argument('--use-tta', action='store_true', 
                               help='Use test-time augmentation for separation')
    parser_convert.add_argument('--batch-size', type=int, default=4, 
                               help='Batch size for separation models')
    
    # Volume controls
    parser_convert.add_argument('--vocals-volume', type=float, default=0.0, 
                               help='Vocals volume adjustment in dB')
    parser_convert.add_argument('--instrumentals-volume', type=float, default=0.0, 
                               help='Instrumentals volume adjustment in dB')
    parser_convert.add_argument('--backing-vocals-volume', type=float, default=0.0, 
                               help='Backing vocals volume adjustment in dB')
    
    # Export format
    parser_convert.add_argument('--export-format-final', default='flac', 
                               choices=['wav', 'flac', 'mp3', 'ogg'], 
                               help='Final export format')
    
    # Hardware
    parser_convert.add_argument('--devices', default='0', 
                               help='GPU devices to use (e.g., "0" or "0 1" for multiple)')
    
    # RVC parameters
    parser_convert.add_argument('--pitch', type=int, default=0, 
                               help='Pitch adjustment (semitones)')
    parser_convert.add_argument('--filter-radius', type=int, default=3, 
                               help='Filter radius for pitch extraction')
    parser_convert.add_argument('--index-rate', type=float, default=0.5, 
                               help='Index rate for voice conversion')
    parser_convert.add_argument('--rms-mix-rate', type=float, default=0.25, 
                               help='RMS mix rate for volume envelope')
    parser_convert.add_argument('--protect', type=float, default=0.33, 
                               help='Protect value for conversion')
    parser_convert.add_argument('--pitch-extract', default='rmvpe', 
                               choices=['crepe', 'rmvpe', 'fcpe', 'harvest', 'onnxcrepe'], 
                               help='Pitch extraction method')
    parser_convert.add_argument('--hop-length', type=int, default=128, 
                               help='Hop length for pitch extraction')
    parser_convert.add_argument('--embedder-model', default='contentvec', 
                               choices=['contentvec', 'hubert', 'crepe', 'rmvpe', 'fcpe', 'harvest', 'onnxcrepe'], 
                               help='Embedder model to use')
    
    # Reverb parameters
    parser_convert.add_argument('--reverb-room-size', type=float, default=0.5, 
                               help='Reverb room size (0-1)')
    parser_convert.add_argument('--reverb-damping', type=float, default=0.5, 
                               help='Reverb damping (0-1)')
    parser_convert.add_argument('--reverb-wet-gain', type=float, default=0.33, 
                               help='Reverb wet gain (0-1)')
    parser_convert.add_argument('--reverb-dry-gain', type=float, default=0.4, 
                               help='Reverb dry gain (0-1)')
    parser_convert.add_argument('--reverb-width', type=float, default=1.0, 
                               help='Reverb width (0-1)')
    
    # Backing vocals inference
    parser_convert.add_argument('--infer-backing-vocals', action='store_true', 
                               help='Infer backing vocals separately')
    parser_convert.add_argument('--infer-backing-vocals-model', 
                               help='Model for backing vocals inference')
    parser_convert.add_argument('--infer-backing-vocals-index', 
                               help='Index for backing vocals inference')
    parser_convert.add_argument('--change-inst-pitch', type=int, default=0, 
                               help='Change instrumental pitch (semitones)')
    
    # Backing vocals parameters
    parser_convert.add_argument('--pitch-back', type=int, default=0, 
                               help='Pitch for backing vocals')
    parser_convert.add_argument('--filter-radius-back', type=int, default=3, 
                               help='Filter radius for backing vocals')
    parser_convert.add_argument('--index-rate-back', type=float, default=0.5, 
                               help='Index rate for backing vocals')
    parser_convert.add_argument('--rms-mix-rate-back', type=float, default=0.25, 
                               help='RMS mix rate for backing vocals')
    parser_convert.add_argument('--protect-back', type=float, default=0.33, 
                               help='Protect value for backing vocals')
    parser_convert.add_argument('--pitch-extract-back', default='rmvpe', 
                               choices=['crepe', 'rmvpe', 'fcpe', 'harvest'], 
                               help='Pitch extraction for backing vocals')
    parser_convert.add_argument('--hop-length-back', type=int, default=128, 
                               help='Hop length for backing vocals')
    parser_convert.add_argument('--export-format-rvc-back', default='wav', 
                               choices=['wav', 'flac', 'mp3'], 
                               help='Export format for backing vocals')
    parser_convert.add_argument('--split-audio-back', action='store_true', 
                               help='Split audio for backing vocals')
    parser_convert.add_argument('--autotune-back', action='store_true', 
                               help='Apply autotune to backing vocals')
    parser_convert.add_argument('--embedder-model-back', default='contentvec', 
                               choices=['contentvec', 'hubert', 'crepe', 'rmvpe', 'fcpe', 'harvest'], 
                               help='Embedder model for backing vocals')
    
    parser_convert.set_defaults(func=convert_audio)
    
    # Add effects command
    parser_effects = subparsers.add_parser('add-effects', help='Add reverb effects to an audio file')
    parser_effects.add_argument('input_audio', help='Path to input audio file')
    parser_effects.add_argument('--output-path', help='Output file path')
    parser_effects.add_argument('--room-size', type=float, default=0.5, help='Reverb room size (0-1)')
    parser_effects.add_argument('--wet', type=float, default=0.33, help='Wet level (0-1)')
    parser_effects.add_argument('--dry', type=float, default=0.4, help='Dry level (0-1)')
    parser_effects.add_argument('--damping', type=float, default=0.5, help='Damping (0-1)')
    parser_effects.add_argument('--width', type=float, default=1.0, help='Width (0-1)')
    parser_effects.set_defaults(func=add_effects)
    
    # Merge command
    parser_merge = subparsers.add_parser('merge', help='Merge multiple audio files')
    parser_merge.add_argument('--vocals', required=True, help='Path to vocals file')
    parser_merge.add_argument('--instrumental', required=True, help='Path to instrumental file')
    parser_merge.add_argument('--backing-vocals', required=True, help='Path to backing vocals file')
    parser_merge.add_argument('--output-path', help='Output file path')
    parser_merge.add_argument('--vocals-gain', type=float, default=0.0, help='Vocals gain in dB')
    parser_merge.add_argument('--instrumental-gain', type=float, default=0.0, help='Instrumental gain in dB')
    parser_merge.add_argument('--backing-gain', type=float, default=0.0, help='Backing vocals gain in dB')
    parser_merge.add_argument('--format', default='flac', choices=['wav', 'flac', 'mp3', 'ogg'], 
                             help='Output format')
    parser_merge.set_defaults(func=merge_audio)
    
    args = parser.parse_args()
    
    if not hasattr(args, 'func'):
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
