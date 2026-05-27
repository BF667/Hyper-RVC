# Hyper-RVC Settings & Languages Enhancement

## Overview
This document describes the enhanced settings system and multi-language support added to Hyper-RVC.

## New Settings Tab Features

### 🎨 Appearance Tab
- **Theme Selection**: Choose from available Gradio themes
  - Real-time theme preview
  - Persistent theme storage
  - Status feedback on theme change

- **Language Selection**: Select from 8 supported languages
  - 🇺🇸 English (US)
  - 🇧🇷 Português (Brasil)
  - 🇪🇸 Español
  - 🇫🇷 Français
  - 🇩🇪 Deutsch
  - 🇯🇵 日本語
  - 🇰🇷 한국어
  - 🇨🇳 简体中文
  - Status feedback on language change
  - Requires application restart to apply

### 🎵 Audio Processing Tab

#### Default Export Settings
- **Export Format**: WAV, FLAC, MP3, OGG, M4A
- **Sample Rate**: 44100, 48000, 22050, 16000 Hz

#### Default Volume Settings
- **Vocals Volume**: -20 to +10 dB (default: -3 dB)
- **Instrumentals Volume**: -20 to +10 dB (default: -3 dB)
- **Backing Vocals Volume**: -20 to +10 dB (default: -3 dB)

#### Default RVC Settings
- **Pitch**: -24 to +24 semitones (default: 0)
- **Index Rate**: 0 to 1 (default: 0.75)
- **Pitch Extractor**: rmvpe, crepe, fcpe, harvest
- **Embedder Model**: contentvec, hubert

### 💻 Hardware Tab

#### GPU Settings
- **GPU Devices**: Configurable device IDs (e.g., "0" or "0 1")
- **FP16 Enable/Disable**: Toggle FP16 precision for faster inference
- **Memory Guidelines**: Built-in help for GPU memory optimization

#### Processing Settings
- **Batch Size**: 1-32 (default: 4)
- **TTA (Test Time Augmentation)**: Enable for better quality

### ⚙️ Advanced Tab

#### Advanced Options
- **Reverb Room Size**: Default room size for reverb effect
- **Reverb Wet Gain**: Default wet gain for reverb
- **Delete Intermediate Files**: Auto-cleanup toggle
- **Auto-open Browser**: Launch browser on startup toggle

#### Reset Settings
- One-click reset to factory defaults
- Status feedback on reset operation

### ℹ️ About Tab
- Application version and credits
- Feature list
- Links to GitHub and Colab

## Supported Languages

### Language Files Location
`assets/i18n/languages/`

### Available Languages
| Code | Language | Native Name |
|------|----------|-------------|
| en_US | English | English (US) |
| pt_BR | Portuguese | Português (Brasil) |
| es_ES | Spanish | Español |
| fr_FR | French | Français |
| de_DE | German | Deutsch |
| ja_JP | Japanese | 日本語 |
| ko_KR | Korean | 한국어 |
| zh_CN | Chinese (Simplified) | 简体中文 |

### Adding a New Language
1. Create a new JSON file in `assets/i18n/languages/`
2. Name it using the format: `{language_code}_{country_code}.json`
3. Copy all keys from `en_US.json`
4. Translate the values to your target language
5. The language will automatically appear in the settings

Example structure:
```json
{
    "Theme": "Your Translation",
    "Language": "Your Translation",
    ...
}
```

## Configuration File

### Location
`assets/config.json`

### Structure
```json
{
  "theme": {
    "file": null,
    "class": "ParityError/Interstellar"
  },
  "lang": {
    "override": false,
    "selected_lang": "en_US"
  },
  "audio": {
    "default_export_format": "FLAC",
    "default_sample_rate": "44100",
    "default_vocals_volume": -3,
    "default_instrumentals_volume": -3,
    "default_backing_volume": -3,
    "default_pitch": 0,
    "default_index_rate": 0.75,
    "default_pitch_extract": "rmvpe",
    "default_embedder": "contentvec"
  },
  "hardware": {
    "default_devices": "0",
    "default_fp16": true,
    "default_batch_size": 4,
    "default_use_tta": false
  },
  "ui": {
    "auto_open_browser": true,
    "delete_intermediate_files": true
  }
}
```

## Internationalization (i18n) Module

### Updated Features
- Automatic language detection from system locale
- Graceful fallback to English if language not found
- Language reload capability
- Better error handling

### Usage
```python
from assets.i18n.i18n import I18nAuto

i18n = I18nAuto()

# Get translation
text = i18n("Theme")  # Returns translated text

# Get current language
current = i18n.get_current_language()

# Get available languages
languages = i18n.get_available_languages()

# Switch language
i18n.reload_language("es_ES")
```

## Files Modified

### Core Files
- `tabs/settings.py` - Complete rewrite with new settings UI
- `assets/i18n/i18n.py` - Enhanced i18n module
- `assets/config.json` - Extended configuration structure
- `assets/i18n/languages/en_US.json` - Updated with new keys

### New Language Files
- `assets/i18n/languages/es_ES.json` - Spanish
- `assets/i18n/languages/fr_FR.json` - French
- `assets/i18n/languages/de_DE.json` - German
- `assets/i18n/languages/ja_JP.json` - Japanese
- `assets/i18n/languages/ko_KR.json` - Korean
- `assets/i18n/languages/zh_CN.json` - Chinese (Simplified)

## Usage Guide

### Changing Theme
1. Go to Settings tab
2. Select "Appearance" sub-tab
3. Choose a theme from the dropdown
4. Status message confirms the change

### Changing Language
1. Go to Settings tab
2. Select "Appearance" sub-tab
3. Choose a language from the dropdown
4. Status message confirms the change
5. **Restart the application** for changes to take effect

### Configuring Defaults
1. Go to Settings tab
2. Navigate to relevant sub-tab (Audio Processing, Hardware, Advanced)
3. Adjust settings as needed
4. Settings are saved automatically

### Resetting to Defaults
1. Go to Settings tab
2. Select "Advanced" sub-tab
3. Click "Reset All Settings to Defaults"
4. Status message confirms the operation
5. Restart the application

## Benefits

### For Users
- **Personalized Experience**: Customize the UI to your preferences
- **Multi-language Support**: Use the application in your native language
- **Persistent Settings**: Settings are saved and restored
- **Easy Reset**: One-click reset if something goes wrong

### For Developers
- **Extensible**: Easy to add new languages
- **Well-documented**: Clear structure and comments
- **Type-safe**: Type hints throughout the code
- **Error-handling**: Graceful fallbacks and error messages

## Future Enhancements

Potential improvements for future versions:
- [ ] Real-time language switching without restart
- [ ] User presets for different use cases
- [ ] Import/export settings functionality
- [ ] More granular audio processing defaults
- [ ] Additional languages (Italian, Russian, Hindi, Arabic, etc.)
- [ ] Language contribution system for community translations

## Troubleshooting

### Language Not Changing
1. Make sure to restart the application after changing language
2. Check if the language file exists in `assets/i18n/languages/`
3. Verify the language code matches the filename

### Settings Not Saving
1. Check file permissions on `assets/config.json`
2. Ensure the application has write access
3. Try running as administrator (Windows) or with sudo (Linux/Mac)

### Theme Not Applying
1. Some themes may require internet connection to load
2. Check if the theme name is valid
3. Try a different theme to isolate the issue

## Credits
- Original i18n system: ShiromiyaG
- Enhanced settings system: Current development
- Language translations: Community contributions
