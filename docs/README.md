# Hyper-RVC Complete Documentation

> Autonomous AI voice processing platform — covers, TTS, transcription, realtime voice conversion, and audio separation in one unified WebUI.

---

## Table of Contents

- [1. Introduction](#1-introduction)
- [2. Installation](#2-installation)
  - [2.1 Local Installation](#21-local-installation)
  - [2.2 Google Colab](#22-google-colab)
  - [2.3 System Requirements](#23-system-requirements)
- [3. Features & UI Tabs](#3-features--ui-tabs)
  - [3.1 Full Inference](#31-full-inference)
  - [3.2 Realtime Voice Conversion](#32-realtime-voice-conversion)
  - [3.3 TTS Inference](#33-tts-inference)
  - [3.4 Whisper Transcription](#34-whisper-transcription)
  - [3.5 Download Model](#35-download-model)
  - [3.6 Download Music](#36-download-music)
  - [3.7 Settings](#37-settings)
- [4. Download Methods Reference](#4-download-methods-reference)
- [5. Colab Tunnel Options](#5-colab-tunnel-options)
- [6. CLI Usage](#6-cli-usage)
- [7. Architecture](#7-architecture)
- [8. F0 Pitch Extractors](#8-f0-pitch-extractors)
- [9. Troubleshooting](#9-troubleshooting)
- [10. Credits](#10-credits)

---

## 1. Introduction

Hyper-RVC is an autonomous pipeline for creating AI voice covers and processing audio. It is a fork of [RVC-AI-Cover-Maker-UI](https://github.com/Eddycrack864/RVC-AI-Cover-Maker-UI) by ShiromiyaG, built on top of the [Applio](https://github.com/IAHispano/Applio) RVC inference engine, [Vietnamese-RVC](https://github.com/PhamHuynhAnh16/Vietnamese-RVC) pitch extraction methods, and [Music Source Separation Training](https://github.com/ZFTurbo/Music-Source-Separation-Training) models by ZFTurbo. The project provides a single Gradio WebUI that integrates voice conversion, text-to-speech, speech-to-text transcription, realtime voice changing, audio source separation, and model downloading into one unified interface.

### WebUI Tab Structure

```
HyperRVC WebUI
├── Inference/
│   ├── Full Inference
│   ├── Realtime
│   ├── TTS
│   └── Whisper
├── Download/
│   ├── Download Model
│   └── Download Music
└── Settings/
    ├── Appearance
    ├── About
    └── Actions
```

---

## 2. Installation

### 2.1 Local Installation

**Prerequisites:** Python 3.10+, NVIDIA GPU with CUDA (recommended), Git, pip.

```bash
# Clone the repository
git clone https://github.com/BF667-IDLE/Hyper-RVC.git
cd Hyper-RVC

# Install dependencies
pip install -r requirements.txt

# Download F0 predictor and embedder models
python main/utils.py

# Start the WebUI
python app.py
```

**Launch options:**

```bash
python app.py                  # Default (port 7755)
python app.py --port 8080      # Custom port
python app.py --share          # Public Gradio link
python app.py --open           # Open browser automatically
python app.py --port 8080 --share --open   # All options
```

The WebUI will auto-retry on port failures (tries up to 10 consecutive ports starting from the selected one).

### 2.2 Google Colab

Open the Colab notebook directly from the README badge or visit:
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/BF667-IDLE/Hyper-RVC/blob/main/assets/colab.ipynb)

**Install cell** handles everything automatically:
- Clones the repo into `/content/main_program`
- Installs system dependency `portaudio19-dev` (required for realtime voice conversion)
- Installs `uv` and `pyngrok` for fast pip installs and Ngrok tunneling
- Installs all Python requirements via `uv pip install`
- Downloads F0 predictor and embedder models

**Start UI cell** provides 10 tunnel options (see Section 5 for details).

### 2.3 System Requirements

| Component | Minimum | Recommended |
|---|---|---|
| GPU | NVIDIA GPU with CUDA | NVIDIA T4 or better |
| RAM | 8 GB | 16 GB |
| Storage | ~5 GB | 10 GB+ (for models) |
| Python | 3.10 | 3.10 - 3.12 |
| OS | Linux, Windows, macOS | Linux (best compatibility) |

**Note on realtime:** Realtime voice conversion requires `sounddevice` (included in requirements) and the PortAudio C library. On Debian/Ubuntu/Colab: `apt-get install portaudio19-dev`. On macOS: `brew install portaudio`. The app gracefully disables the realtime tab if PortAudio is unavailable.

---

## 3. Features & UI Tabs

### 3.1 Full Inference

The full inference tab provides the complete RVC voice conversion pipeline with audio source separation. It is designed for creating AI covers from existing songs or audio files.

**Audio Separation Models (UVR):**
- Vocals: Mel-Roformer (KimberleyJSN), BS-Roformer (ViperX), MDX23C
- Karaoke: Mel-Roformer Karaoke (aufr33 + viperx), UVR-BVE
- Dereverb: MDX23C Dereverb (aufr33 + jarredou), BS-Roformer Dereverb (anvuew), UVR-Deecho-Dereverb, Reverb HQ (FoxJoy)
- Deecho: UVR-DeEcho-Normal, UVR-DeEcho-Aggressive
- Denoise: Mel-Roformer Denoise Normal/Aggressive (aufr33), UVR-DeNoise

**RVC Parameters:**
- Pitch shift (-12 to +12 semitones)
- Search Feature Ratio / Index Rate (0-1)
- Filter Radius (0-7)
- Protect Voiceless Consonants (0-0.5)
- Silence Threshold
- F0 extraction method (15+ options, see Section 8)
- Embedder model selection
- Autotune toggle

**Additional Controls:**
- Backing vocals inference with independent model selection
- Instrumental pitch shift
- Reverb effects (room size, wet level, damping)
- Multiple export formats: WAV, MP3, FLAC, OGG, M4A
- Action buttons: Refresh, Unload Model, Clear outputs

**File Layout:** Model and index dropdowns are side-by-side in a row for compact layout. All settings are organized in an accordion for clean UI.

### 3.2 Realtime Voice Conversion

Server-mode realtime voice conversion that captures audio from your microphone, processes it through the RVC pipeline, and plays the converted output through your speakers. No UVR/audio separation is applied — input goes directly to RVC for minimal latency.

**Based on:** Concepts from [deiteris/voice-changer](https://github.com/deiteris/voice-changer) with Gradio UI inspired by [Vietnamese-RVC](https://github.com/PhamHuynhAnh16/Vietnamese-RVC), using a simpler single-file architecture.

**Audio Device Configuration:**
- Input device (microphone) and output device (speakers) dropdowns
- Refresh Devices button to rescan available hardware
- Input gain control (0-3x)
- Block size tuning (512-8192) — smaller blocks are more responsive but heavier on GPU

**RVC Settings (same as full inference):**
- Pitch, index rate, filter radius, protect consonants, silence threshold
- Pitch extractor, embedder model, autotune
- All parameters support hot-swapping while the engine is running

**Status Display:**
- Uses `gr.Label()` to show realtime status as key-value pairs
- Shows: status (Ready/Running/Stopped), latency in ms, volume in dB
- Start/Stop/Unload Model buttons

**Requirements:**
- `sounddevice` Python package (in requirements.txt)
- PortAudio C library (`apt-get install portaudio19-dev` on Linux/Colab)
- Gracefully deactivates if unavailable (catches both `ImportError` and `OSError`)

### 3.3 TTS Inference

Text-to-Speech generation using Microsoft Edge TTS with optional RVC voice conversion on the output.

**Features:**
- 400+ Azure neural voices across 100+ languages
- Adjustable speech rate (-30% to +30%)
- Character counter (max 5000 characters)
- Full RVC parameter control for voice conversion
- Two-stage output: TTS audio first, then TTS+RVC converted audio
- Multiple export formats: WAV, MP3, FLAC, OGG, M4A

**Workflow:** Enter text → Select voice and language → Generate TTS → (Optional) Apply RVC voice conversion → Export.

### 3.4 Whisper Transcription

Speech-to-text transcription powered by OpenAI Whisper with speaker diarization support.

**Features:**
- 99+ language support with automatic language detection
- Word-level timestamps for precise alignment
- Output formats: TXT, JSON, SRT, VTT
- Model selection: tiny, base, small, medium, large, large-v2, large-v3
- GPU acceleration for faster processing
- Speaker diarization via SpeechBrain and ECAPA-TDNN embeddings

**Use Cases:** Subtitle generation, interview transcription, lyric extraction, content indexing, accessibility.

### 3.5 Download Model

Download RVC voice models from multiple sources with a unified interface and method selection.

**9 Download Methods:**

| Method | Source | URL Pattern | Description |
|---|---|---|---|
| `auto` | Auto-detect | Any | Automatically detects source from URL pattern |
| `gdrive` | Google Drive | `drive.google.com` | Downloads via gdown with confirmation page handling |
| `huggingface` | HuggingFace | `huggingface.co` | Supports `/blob/`, `/resolve/`, `/tree/` URLs |
| `mediafire` | MediaFire | `mediafire.com` | Parses download button from page |
| `pixeldrain` | PixelDrain | `pixeldrain.com` | Downloads via PixelDrain API |
| `yandex` | Yandex Disk | `disk.yandex.ru` | Uses Yandex public resource API |
| `discord` | Discord CDN | `cdn.discordapp.com` | Direct streaming download |
| `applio` | Applio.org | `applio.org` | Resolves model link via Supabase API |
| `direct` | Any URL | Any | Generic streaming download (fallback) |

**UI Features:**
- Method selector dropdown with descriptions for each method
- Auto-detect button — paste a URL and click to auto-select the correct method
- URL input and method selector side-by-side in a row
- Fast downloads with 8 MB chunk streaming and tqdm progress bars
- Automatic zip extraction to `logs/` directory
- Drag-and-drop file upload for `.pth` and `.index` files

### 3.6 Download Music

Download audio from YouTube and 1000+ supported sites using yt-dlp. Audio files are saved to `audio_files/original_files/` with metadata preserved.

### 3.7 Settings

Three sub-tabs for application configuration:

- **Appearance:** Theme selection with live preview
- **About:** App credits, version info, project links
- **Actions:** App management buttons

---

## 4. Download Methods Reference

### Auto-Detection Logic

The `auto` method inspects the URL hostname to select the appropriate downloader:

```
drive.google.com    → gdrive
huggingface.co      → huggingface
mediafire.com       → mediafire
pixeldrain.com      → pixeldrain
disk.yandex.ru      → yandex
cdn.discordapp.com  → discord
applio.org          → applio
(any other)         → direct
```

### Error Handling

- **Google Drive quota exceeded:** "Too many users have viewed or downloaded this file recently" — try again later or use a different link
- **Private GDrive link:** "Cannot retrieve the public link of the file" — set the file to "Anyone with the link"
- **HuggingFace tree page:** Scans for `.zip` download links; if none found, reports an error
- **Network timeouts:** All requests use 30-second timeouts to avoid hanging

### Download Pipeline

```
URL → Method Detection → Platform-specific Download → Stream to zips/ → Extract to logs/
```

All streaming downloads use **8 MB chunks** with tqdm progress bars for speed and visibility.

---

## 5. Colab Tunnel Options

The Colab notebook provides 3 tunnel types so you can always get a public link even if one service is down.

| Tunnel | Install Required | Auth Required | Domain | Notes |
|---|---|---|---|---|
| Gradio | No | No | `*.gradio.live` | Built-in `--share`, simplest option |
| Ngrok | `pip install pyngrok` | Authtoken from dashboard | `*.ngrok-free.app` | Region selection for lower latency |
| Cloudflare | `wget cloudflared` binary | No | `*.trycloudflare.com` | Fast, no account needed |

**Usage:** For tunnels other than Gradio, wait for the Local URL to appear first, then use the displayed Public URL.

---

## 6. CLI Usage

Hyper-RVC includes a CLI interface via `cli.py` for command-line audio processing.

```bash
# List available RVC models
python cli.py list-models

# Download a model
python cli.py download-model --link https://huggingface.co/username/model

# Download music from YouTube
python cli.py download-music --link https://youtube.com/watch?v=...

# Basic voice conversion
python cli.py convert --model-path /path/to/model.pth --input-audio song.mp3

# Full conversion with all options
python cli.py convert --model-path model.pth --index-path index.pth \
  --input-audio song.mp3 --pitch 12 --reverb --denoise \
  --vocal-model "Mel-Roformer by KimberleyJSN" \
  --export-format-final mp3

# Add audio effects
python cli.py add-effects input.wav --room-size 0.8 --wet 0.4 --output-path output.wav

# Merge audio files
python cli.py merge \
  --vocals vocals.flac \
  --instrumental instrumental.flac \
  --backing-vocals backing.flac \
  --format mp3

# Show current configuration
python cli.py show-config
```

---

## 7. Architecture

### File Structure

```
Hyper-RVC/
├── app.py                          # Main WebUI entry point (Gradio)
├── main.py                         # Legacy entry point (imports from app.py)
├── core.py                         # Backward-compatible shim
├── cli.py                          # CLI interface
├── requirements.txt                # Python dependencies
│
├── main/                           # Core processing modules
│   ├── __init__.py                 # Package init + audioop 3.13 shim + re-exports
│   ├── core.py                     # Pipeline orchestrator (full_inference_program)
│   ├── utils.py                    # Predictor/embedder bulk download
│   │
│   ├── uvr/                        # Audio separation
│   │   ├── separator.py            # High-level separation functions
│   │   └── models/                 # Model architectures (BS-Roformer, Bandit, SCNet, etc.)
│   │
│   ├── rvc/                        # RVC voice conversion (Applio engine)
│   │   ├── converter.py            # High-level RVC wrapper
│   │   └── engine/                 # Inference engine, predictors, algorithms
│   │
│   ├── tts/                        # Text-to-Speech (Edge TTS + RVC)
│   │   └── synthesis.py
│   │
│   ├── whisper/                    # Whisper transcription + diarization
│   │   ├── transcriber.py
│   │   └── diarization/
│   │
│   ├── realtime/                   # Realtime voice conversion engine
│   │
│   └── tools/                      # Shared utilities
│       ├── variables.py            # Centralized config (F0 methods, URLs, models)
│       ├── downloader.py           # Multi-method model download orchestration
│       ├── gdown.py                # Google Drive downloader
│       ├── hf.py                   # HuggingFace downloader
│       ├── mediafire.py            # MediaFire downloader
│       ├── file_utils.py           # File search, model lookup
│       ├── audio_utils.py          # Audio effects, merging
│       ├── config.py               # Configuration management
│       └── logger.py               # Logging utilities
│
├── tabs/                           # Gradio UI tabs
│   ├── full_inference.py           # Voice Conversion tab
│   ├── realtime_tab.py             # Realtime Voice Conversion tab
│   ├── tts_inference.py            # TTS Generation tab
│   ├── whisper_transcription.py    # Transcription tab
│   ├── download_model.py           # Download Model tab (method selector)
│   ├── download_music.py           # Download Music tab
│   └── settings.py                 # Settings tab (Appearance, About, Actions)
│
├── assets/
│   ├── themes/                     # Gradio theme JSON files
│   ├── i18n/                       # Internationalization (60+ languages)
│   ├── colab.ipynb                 # Google Colab notebook
│   ├── logo.ico                    # Favicon
│   └── config.json                 # User settings
│
├── docs/                           # Documentation
├── tests/                          # Test suite
├── run.sh / run.bat                # Launch scripts
└── update.sh / update.bat          # Update scripts
```

### Key Modules

**`main/tools/variables.py`** — Single source of truth for all configuration:
- F0 method lists (`F0_METHODS`, `F0_METHODS_UI`) and model file mapping
- Predictor and embedder download URLs (`PREDICTORS_URL_BASE`, `EMBEDDERS_URL_BASE`)
- UVR separation model definitions (vocals, karaoke, dereverb, deecho, denoise)
- FP16 support detection for GPU compatibility

**`main/tools/downloader.py`** — Multi-method download system:
- 9 download methods with auto-detection from URL patterns
- 8 MB chunk streaming for fast downloads with tqdm progress
- Automatic zip extraction and model folder normalization
- Platform-specific error handling (GDrive quota, private links, etc.)

**`app.py`** — WebUI entry point:
- Gradio Blocks with tab groups: Inference (4 sub-tabs), Download (2 sub-tabs), Settings (3 sub-tabs)
- Auto-retry port on launch failure
- Theme loading from JSON config

### Data Flow

```
Audio Input
    │
    ├── UVR Separation (vocals, instrumental, karaoke, dereverb, denoise)
    │       │
    │       └── Mel-Roformer / BS-Roformer / MDX23C / Bandit / SCNet / Demucs
    │
    ├── RVC Voice Conversion
    │       │
    │       ├── Embedder: contentvec / hubert-base (zh/ja/ko)
    │       ├── F0 Extractor: rmvpe / crepe / fcpe / harvest / etc.
    │       └── Generator + Synthesizer → Converted Audio
    │
    ├── TTS (text → Edge TTS → audio → optional RVC)
    │
    └── Whisper (audio → transcription → TXT/JSON/SRT/VTT)
```

---

## 8. F0 Pitch Extractors

Hyper-RVC supports 15+ pitch extraction methods, including hybrid combinations that blend two extractors for improved accuracy.

### Standard Methods

| Method | Type | Quality | Speed | Description |
|---|---|---|---|---|
| `rmvpe` | Neural | High | Medium | Robust vocal pitch estimation, recommended default |
| `crepe` | Neural | Very High | Slow | Full CREPE model, most accurate |
| `crepe-tiny` | Neural | Good | Medium | Smaller CREPE model, faster than full |
| `fcpe` | Neural | High | Fast | Fundamental frequency contour extraction |
| `fcpe-legacy` | Neural | High | Fast | Legacy FCPE implementation |
| `onnxcrepe` | ONNX | Very High | Medium | CREPE via ONNX Runtime |
| `harvest` | Signal | Medium | Slow | Traditional signal processing method |
| `mangio-crepe` | Neural | Very High | Slow | CREPE with Mangio improvements |
| `mangio-crepe-tiny` | Neural | Good | Medium | Tiny Mangio CREPE |
| `hpa-rmvpe` | Neural | High | Medium | HPa variant of RMVPE |
| `swipe` | Neural | High | Medium | SWIPE pitch estimation |
| `penn` | ONNX | High | Fast | PENN pitch estimator via ONNX |
| `mangio-penn` | ONNX | High | Fast | PENN with Mangio improvements |
| `djcm` | Neural | High | Fast | DJCM pitch contour model |
| `djcm-svs` | Neural | High | Fast | DJCM singing voice specific |
| `swift` | ONNX | High | Fast | SWIFT pitch estimator via ONNX |
| `pesto` | ONNX | High | Fast | PESTO pitch estimation via ONNX |

### Hybrid Methods

Combine two extractors for improved results:

| Method | Combination |
|---|---|
| `hybrid[crepe+rmvpe]` | CREPE + RMVPE |
| `hybrid[crepe+fcpe]` | CREPE + FCPE |
| `hybrid[rmvpe+fcpe]` | RMVPE + FCPE |
| `hybrid[rmvpe+hpa-rmvpe]` | RMVPE + HPa-RMVPE |
| `hybrid[crepe+hpa-rmvpe]` | CREPE + HPa-RMVPE |
| `hybrid[rmvpe+penn]` | RMVPE + PENN |

### Configuration

All F0 model paths and defaults are centralized in `main/tools/variables.py`. Models are auto-downloaded from HuggingFace (`NeoPy/Ultimate-Models`) on first use via `python main/utils.py`.

Default F0 parameters:
- `f0_min`: 50 Hz
- `f0_max`: 1100 Hz
- `sample_rate`: 16000 Hz
- `crepe_threshold`: 0.03
- `rmvpe_threshold`: 0.03
- `fcpe_threshold`: 0.03

---

## 9. Troubleshooting

### PortAudio / sounddevice Errors

**Error:** `OSError: PortAudio library not found`

The `sounddevice` Python package requires the PortAudio C library installed on your system. The realtime tab gracefully deactivates if PortAudio is missing (both `ImportError` and `OSError` are caught).

**Fix:**
```bash
# Linux / Colab
sudo apt-get install portaudio19-dev

# macOS
brew install portaudio

# Windows — PortAudio is bundled with the sounddevice wheel
pip install sounddevice
```

### Google Drive Download Errors

**Error:** "Too many users have viewed or downloaded this file recently"

Google Drive enforces download quotas on frequently accessed files. Wait a few hours and try again, or re-upload the file to your own Google Drive.

**Error:** "Cannot retrieve the public link of the file"

The file permissions are set to restricted. Go to the file in Google Drive, right-click > Share > Change to "Anyone with the link."

### Model Not Found

If the model dropdown is empty or your model is missing:
1. Click **Refresh Models** in the inference tab
2. Verify the model files (`.pth` and optionally `.index`) are in the `logs/` directory
3. For downloaded models, check that the zip extraction completed successfully
4. Try downloading the model again using the Download Model tab

### CUDA Out of Memory

- **Full Inference:** Use a smaller vocal separation model (MDX23C instead of Mel-Roformer)
- **Realtime:** Reduce the block size (try 1024 or 512) to lower GPU memory usage
- **General:** Close other GPU-consuming applications; restart the runtime on Colab

### Python 3.13 Compatibility

Python 3.13 removed the `audioop` module which `pydub` depends on. Hyper-RVC includes a transparent shim in `main/__init__.py` that automatically substitutes `audioop-lts` when running on Python 3.13+. The `requirements.txt` includes `audioop-lts` as a conditional dependency.

### Whisper Errors

- **Model download fails:** Ensure `huggingface-hub` is installed and you have internet access. Whisper models are downloaded from HuggingFace on first use.
- **Transcription is slow:** Select a smaller model (tiny or base) or ensure GPU acceleration is available.

---

## 10. Credits

### Project Team

| Role | Member | Description |
|---|---|---|
| Base Project Owner | [ShiromiyaG](https://github.com/ShiromiyaG) | Owner of RVC-AI-Cover-Maker-UI |
| Base Project Contributor | [Eddycrack864](https://github.com/Eddycrack864) | Contributor to RVC-AI-Cover-Maker-UI |
| Fork Owner & Maintainer | [BF667-IDLE](https://github.com/BF667-IDLE) | Hyper-RVC fork, UI restructuring, new features |
| Colab UI & Tunnels | [Nick088](https://linktr.ee/Nick088) | Colab notebook, 10 tunnel types, local setup |
| QA Testing | [FullmatheusBallZ](https://www.youtube.com/@FullmatheusBallZ) | Google Colab testing & quality assurance |

### Core Projects & Libraries

| Project | Author | Role |
|---|---|---|
| [RVC-AI-Cover-Maker-UI](https://github.com/Eddycrack864/RVC-AI-Cover-Maker-UI) | ShiromiyaG | Original UI framework & cover pipeline |
| [Applio](https://github.com/IAHispano/Applio) | IAHispano | RVC inference engine, pitch extraction |
| [Vietnamese-RVC](https://github.com/PhamHuynhAnh16/Vietnamese-RVC) | PhamHuynhAnh16 | RVC library, additional F0 predictors |
| [Music Source Separation Training](https://github.com/ZFTurbo/Music-Source-Separation-Training) | ZFTurbo | BS-Roformer, Mel-Roformer, SCNet, MDX23C, Bandit |
| [voice-changer](https://github.com/deiteris/voice-changer) | deiteris | Realtime voice changer concepts |
| [Ultimate Vocal Remover](https://github.com/Anjok07/ultimatevocalremovergui) | Anjok07 | UVR model weights & architectures |
| [Whisper](https://github.com/openai/whisper) | OpenAI | Speech recognition & transcription |
| [SpeechBrain](https://github.com/speechbrain/speechbrain) | SpeechBrain Team | Speaker diarization & ECAPA-TDNN |
| [Edge TTS](https://github.com/rany2/edge-tts) | rany2 | 400+ Azure voices |
| [Audio Separator](https://github.com/karaokenerds/python-audio-separator) | beveradb | Python audio separation wrapping UVR models |
