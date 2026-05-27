"""
Unit tests for Hyper-RVC core functions.

Run with: python -m pytest tests/test_core.py -v
"""

import os
import sys
import pytest
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main.tools.config import Config, get_config, load_config, DEFAULT_CONFIG
from main.tools.logger import setup_logger, get_logger


class TestConfig:
    """Tests for configuration management."""
    
    def test_config_initialization(self):
        """Test that Config initializes with default values."""
        config = Config()
        assert config.config is not None
        assert "audio" in config.config
        assert "models" in config.config
    
    def test_config_get_nested_value(self):
        """Test getting nested configuration values using dot notation."""
        config = Config()
        pitch = config.get("audio.pitch")
        assert pitch == 0
        
        vocal_model = config.get("models.vocal_model")
        assert vocal_model == "Mel-Roformer by KimberleyJSN"
    
    def test_config_get_with_default(self):
        """Test getting non-existent key returns default value."""
        config = Config()
        value = config.get("nonexistent.key", "default")
        assert value == "default"
    
    def test_config_set_value(self):
        """Test setting configuration values."""
        config = Config()
        config.set("audio.pitch", 5)
        assert config.get("audio.pitch") == 5
        
        config.set("new_key", "new_value")
        assert config.get("new_key") == "new_value"
    
    def test_config_reset_to_defaults(self):
        """Test resetting configuration to defaults."""
        config = Config()
        config.set("audio.pitch", 10)
        assert config.get("audio.pitch") == 10
        
        config.reset_to_defaults()
        assert config.get("audio.pitch") == 0
    
    def test_config_property_accessors(self):
        """Test property accessors for config sections."""
        config = Config()
        assert isinstance(config.audio, dict)
        assert isinstance(config.models, dict)
        assert isinstance(config.hardware, dict)
        assert isinstance(config.ui, dict)
    
    def test_config_save_and_load(self, tmp_path):
        """Test saving and loading configuration from file."""
        config_path = tmp_path / "test_config.json"
        config = Config(str(config_path))
        
        # Modify config
        config.set("audio.pitch", 7)
        config.set("ui.port", 8888)
        
        # Save config
        config.save()
        assert config_path.exists()
        
        # Load config in new instance
        new_config = Config(str(config_path))
        assert new_config.get("audio.pitch") == 7
        assert new_config.get("ui.port") == 8888
    
    def test_config_merge_with_user_config(self, tmp_path):
        """Test that user config merges with defaults."""
        config_path = tmp_path / "test_config.json"
        
        # Create partial config
        partial_config = {
            "ui": {"port": 9999}
        }
        
        import json
        with open(config_path, 'w') as f:
            json.dump(partial_config, f)
        
        config = Config(str(config_path))
        
        # Should have user value
        assert config.get("ui.port") == 9999
        
        # Should still have default values for other keys
        assert config.get("audio.pitch") == 0
        assert config.get("models.vocal_model") == "Mel-Roformer by KimberleyJSN"


class TestLogger:
    """Tests for logging utilities."""
    
    def test_logger_setup(self):
        """Test that logger sets up correctly."""
        logger = setup_logger("test_logger", log_to_file=False)
        assert logger is not None
        assert logger.name == "test_logger"
    
    def test_logger_get_logger(self):
        """Test getting logger instance."""
        logger = get_logger("test_module")
        assert logger is not None
    
    def test_logger_creates_log_directory(self, tmp_path):
        """Test that logger creates log directory."""
        log_dir = tmp_path / "logs"
        logger = setup_logger(
            "test_logger",
            log_dir=str(log_dir),
            log_to_file=True
        )
        
        assert log_dir.exists()
    
    def test_logger_no_duplicate_handlers(self):
        """Test that logger doesn't add duplicate handlers."""
        logger = setup_logger("test_no_dup", log_to_file=False)
        initial_handler_count = len(logger.handlers)
        
        # Call setup again
        logger2 = setup_logger("test_no_dup", log_to_file=False)
        
        assert len(logger2.handlers) == initial_handler_count


class TestHelperFunctions:
    """Tests for helper functions in core module."""
    
    def test_get_model_info_by_name_found(self):
        """Test finding model info by name."""
        from core import get_model_info_by_name
        
        model_info = get_model_info_by_name("Mel-Roformer by KimberleyJSN")
        assert model_info is not None
        assert model_info["name"] == "Mel-Roformer by KimberleyJSN"
    
    def test_get_model_info_by_name_not_found(self):
        """Test finding non-existent model."""
        from core import get_model_info_by_name
        
        model_info = get_model_info_by_name("NonExistentModel")
        assert model_info is None
    
    def test_get_last_modified_file(self, tmp_path):
        """Test getting most recently modified file."""
        from core import get_last_modified_file
        
        # Create test files
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        
        file1.write_text("content1")
        import time
        time.sleep(0.1)
        file2.write_text("content2")
        
        result = get_last_modified_file(str(tmp_path))
        assert result == "file2.txt"
    
    def test_get_last_modified_file_empty_directory(self, tmp_path):
        """Test getting file from empty directory."""
        from core import get_last_modified_file
        
        result = get_last_modified_file(str(tmp_path))
        assert result is None
    
    def test_get_last_modified_file_invalid_directory(self):
        """Test getting file from invalid directory."""
        from core import get_last_modified_file
        
        with pytest.raises(NotADirectoryError):
            get_last_modified_file("/nonexistent/path")
    
    def test_search_with_word(self, tmp_path):
        """Test searching for file with specific word."""
        from core import search_with_word
        
        # Create test files
        (tmp_path / "test_vocals.txt").write_text("content")
        (tmp_path / "test_instrumental.txt").write_text("content")
        
        result = search_with_word(str(tmp_path), "vocals")
        assert result is not None
        assert "vocals" in result
    
    def test_search_with_word_not_found(self, tmp_path):
        """Test searching for non-existent word."""
        from core import search_with_word
        
        (tmp_path / "test_file.txt").write_text("content")
        
        result = search_with_word(str(tmp_path), "nonexistent")
        assert result is None
    
    def test_search_with_two_words(self, tmp_path):
        """Test searching for file with two words."""
        from core import search_with_two_words
        
        (tmp_path / "test_vocals_final.txt").write_text("content")
        (tmp_path / "test_vocals.txt").write_text("content")
        
        result = search_with_two_words(str(tmp_path), "vocals", "final")
        assert result is not None
        assert "vocals" in result and "final" in result


class TestAudioEffects:
    """Tests for audio effects functions."""
    
    def test_merge_audios_file_not_found(self):
        """Test merge_audios with non-existent files."""
        from core import merge_audios
        
        with pytest.raises(FileNotFoundError):
            merge_audios(
                vocals_path="/nonexistent/vocals.flac",
                inst_path="/nonexistent/inst.flac",
                backing_path="/nonexistent/backing.flac",
                output_path="/nonexistent/output.flac",
                main_gain=0.0,
                inst_gain=0.0,
                backing_Vol=0.0,
                output_format="flac"
            )


class TestCLIValidation:
    """Tests for CLI validation functions."""
    
    def test_validate_audio_file_not_exists(self):
        """Test validation fails for non-existent file."""
        from cli import validate_audio_file
        import argparse
        
        with pytest.raises(argparse.ArgumentTypeError):
            validate_audio_file("/nonexistent/file.mp3")
    
    def test_validate_positive_int(self):
        """Test positive integer validation."""
        from cli import validate_positive_int
        import argparse
        
        assert validate_positive_int("5") == 5
        assert validate_positive_int("1") == 1
        
        with pytest.raises(argparse.ArgumentTypeError):
            validate_positive_int("0")
        
        with pytest.raises(argparse.ArgumentTypeError):
            validate_positive_int("-5")
        
        with pytest.raises(argparse.ArgumentTypeError):
            validate_positive_int("abc")
    
    def test_validate_float_range(self):
        """Test float range validation."""
        from cli import validate_float_range
        import argparse
        
        # Valid values
        assert validate_float_range("0.5", 0.0, 1.0, "test") == 0.5
        assert validate_float_range("0.0", 0.0, 1.0, "test") == 0.0
        assert validate_float_range("1.0", 0.0, 1.0, "test") == 1.0
        
        # Out of range
        with pytest.raises(argparse.ArgumentTypeError):
            validate_float_range("1.5", 0.0, 1.0, "test")
        
        with pytest.raises(argparse.ArgumentTypeError):
            validate_float_range("-0.1", 0.0, 1.0, "test")
        
        # Invalid format
        with pytest.raises(argparse.ArgumentTypeError):
            validate_float_range("abc", 0.0, 1.0, "test")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
