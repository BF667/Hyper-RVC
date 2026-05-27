"""
Internationalization (i18n) module for Hyper-RVC.

Provides automatic language detection and translation capabilities
with support for multiple languages.
"""

import os
import sys
import json
from pathlib import Path
from locale import getdefaultlocale
from typing import Optional, List, Dict

now_dir = os.getcwd()
sys.path.append(now_dir)


class I18nAuto:
    """
    Automatic internationalization handler.
    
    Loads and manages translations for multiple languages.
    Supports automatic language detection based on system locale.
    """
    LANGUAGE_PATH = os.path.join(now_dir, "assets", "i18n", "languages")

    def __init__(self, language: Optional[str] = None):
        """
        Initialize the i18n handler.
        
        Args:
            language: Optional language code to force (e.g., 'en_US', 'es_ES')
        """
        with open(
            os.path.join(now_dir, "assets", "config.json"), "r", encoding="utf8"
        ) as file:
            config = json.load(file)
            override = config["lang"]["override"]
            lang_prefix = config["lang"]["selected_lang"]

        self.language = lang_prefix

        if override == False:
            language = language or getdefaultlocale()[0]
            lang_prefix = language[:2] if language is not None else "en"
            available_languages = self._get_available_languages()
            matching_languages = [
                lang for lang in available_languages if lang.startswith(lang_prefix)
            ]
            self.language = matching_languages[0] if matching_languages else "en_US"

        self.language_map = self._load_language_list()
        
        print(f"Loaded language: {self.language}")

    def _load_language_list(self) -> Dict[str, str]:
        """
        Load the language translation map from JSON file.
        
        Returns:
            Dictionary mapping English keys to translated values
        """
        try:
            file_path = Path(self.LANGUAGE_PATH) / f"{self.language}.json"
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Warning: Language file {self.language}.json not found, falling back to English")
            self.language = "en_US"
            file_path = Path(self.LANGUAGE_PATH) / "en_US.json"
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)

    def _get_available_languages(self) -> List[str]:
        """
        Get list of available language codes.
        
        Returns:
            List of available language codes (e.g., ['en_US', 'es_ES', ...])
        """
        language_files = [path.stem for path in Path(self.LANGUAGE_PATH).glob("*.json")]
        return language_files

    def _language_exists(self, language: str) -> bool:
        """
        Check if a language file exists.
        
        Args:
            language: Language code to check
            
        Returns:
            True if language file exists, False otherwise
        """
        return (Path(self.LANGUAGE_PATH) / f"{language}.json").exists()

    def reload_language(self, language: str) -> bool:
        """
        Reload translations for a different language.
        
        Args:
            language: Language code to switch to
            
        Returns:
            True if successful, False otherwise
        """
        if self._language_exists(language):
            self.language = language
            self.language_map = self._load_language_list()
            print(f"Language switched to: {language}")
            return True
        return False

    def __call__(self, key: str) -> str:
        """
        Get translation for a key.
        
        Args:
            key: Translation key (English text)
            
        Returns:
            Translated text or original key if not found
        """
        return self.language_map.get(key, key)
    
    def get_current_language(self) -> str:
        """
        Get the current language code.
        
        Returns:
            Current language code (e.g., 'en_US')
        """
        return self.language
    
    def get_available_languages(self) -> List[str]:
        """
        Get list of available language codes.
        
        Returns:
            List of available language codes
        """
        return self._get_available_languages()
