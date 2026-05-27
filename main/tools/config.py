"""
Configuration module for Hyper-RVC.

Provides default settings and configuration management for the application.
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path


# Default configuration
DEFAULT_CONFIG = {
    # General settings
    "project_name": "Hyper-RVC",
    "version": "1.0.0",
    
    # Audio processing defaults
    "audio": {
        "default_export_format": "flac",
        "default_sample_rate": 44100,
        "default_channels": 2,
        
        # Volume defaults (in dB)
        "vocals_volume": -3.0,
        "instrumentals_volume": -3.0,
        "backing_vocals_volume": -3.0,
        
        # RVC defaults
        "pitch": 0,
        "filter_radius": 3,
        "index_rate": 0.75,
        "rms_mix_rate": 0.25,
        "protect": 0.33,
        "pitch_extract": "rmvpe",
        "hop_length": 64,
        "embedder_model": "contentvec",
        
        # Audio separation
        "split_audio": False,
        "autotune": False,
        "use_tta": False,
        "batch_size": 1,
        
        # Effects
        "reverb": False,
        "reverb_room_size": 0.5,
        "reverb_damping": 0.5,
        "reverb_wet_gain": 0.33,
        "reverb_dry_gain": 0.4,
        "reverb_width": 1.0,
        
        # Processing options
        "deecho": True,
        "denoise": False,
        "delete_intermediate_audios": True,
    },
    
    # Model defaults
    "models": {
        "vocal_model": "Mel-Roformer by KimberleyJSN",
        "karaoke_model": "Mel-Roformer Karaoke by aufr33 and viperx",
        "dereverb_model": "UVR-Deecho-Dereverb",
        "deecho_model": "UVR-Deecho-Normal",
        "denoise_model": "Mel-Roformer Denoise Normal by aufr33",
    },
    
    # Hardware settings
    "hardware": {
        "devices": "0",
        "force_cpu": False,
        "fp16": True,
    },
    
    # Backing vocals settings
    "backing_vocals": {
        "infer": False,
        "pitch": 0,
        "filter_radius": 3,
        "index_rate": 0.75,
        "rms_mix_rate": 0.25,
        "protect": 0.33,
        "pitch_extract": "rmvpe",
        "hop_length": 64,
        "embedder_model": "contentvec",
        "split_audio": False,
        "autotune": False,
        "export_format": "wav",
    },
    
    # Directory settings
    "directories": {
        "models": "models",
        "audio_files": "audio_files",
        "logs": "logs",
        "outputs": "audio_files/outputs",
    },
    
    # UI settings
    "ui": {
        "theme": "ParityError/Interstellar",
        "port": 7755,
        "max_port_attempts": 10,
        "share": False,
        "inbrowser": True,
    },
}


class Config:
    """Configuration manager for Hyper-RVC."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Optional path to custom configuration file
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config = DEFAULT_CONFIG.copy()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        now_dir = os.getcwd()
        return os.path.join(now_dir, "config_hyper_rvc.json")
    
    def _load_config(self) -> None:
        """Load configuration from file if it exists."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    self._merge_config(user_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config file: {e}")
    
    def _merge_config(self, user_config: Dict[str, Any]) -> None:
        """
        Merge user configuration with defaults.
        
        Args:
            user_config: User-provided configuration dictionary
        """
        for key, value in user_config.items():
            if key in self.config and isinstance(value, dict) and isinstance(self.config[key], dict):
                self.config[key].update(value)
            else:
                self.config[key] = value
    
    def save(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving config file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Supports dot notation for nested keys (e.g., "audio.pitch").
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Supports dot notation for nested keys.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self.config = DEFAULT_CONFIG.copy()
    
    @property
    def audio(self) -> Dict[str, Any]:
        """Get audio configuration."""
        return self.config.get("audio", {})
    
    @property
    def models(self) -> Dict[str, Any]:
        """Get models configuration."""
        return self.config.get("models", {})
    
    @property
    def hardware(self) -> Dict[str, Any]:
        """Get hardware configuration."""
        return self.config.get("hardware", {})
    
    @property
    def ui(self) -> Dict[str, Any]:
        """Get UI configuration."""
        return self.config.get("ui", {})


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from a file.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        Config instance
    """
    global _config
    _config = Config(config_path)
    return _config
