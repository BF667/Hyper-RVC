<div align="center">

# Hyper RVC WebUI

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/BF667/Hyper-RVC/blob/main/assets/colab.ipynb)

An autonomous pipeline to create covers with any RVC v2 trained AI voice from YouTube videos or a local audio file, plus **ACE-Step 1.5** text-to-music generation built right in. For developers who may want to add a singing functionality into their AI assistant/chatbot/vtuber, for people who want to hear their favourite characters sing their favourite song, or for anyone who wants to generate original music from text prompts.

---

</div>

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start the WebUI
python app.py

# With custom options
python app.py --port 8080 --share --open
```

## CLI Usage

### List available models

```bash
python cli.py list-models
```

### Download a model

```bash
python cli.py download-model --link https://huggingface.co/username/model
```

### Download music from YouTube

```bash
python cli.py download-music --link https://youtube.com/watch?v=...
```

### Basic audio conversion

```bash
python cli.py convert --model-path /path/to/model.pth --input-audio song.mp3
```

### Full conversion with all options

```bash
python cli.py convert --model-path model.pth --index-path index.pth \
  --input-audio song.mp3 --pitch 12 --reverb --denoise \
  --vocal-model "Mel-Roformer by KimberleyJSN" \
  --export-format-final mp3
```

### Add Effect

```bash
python cli.py add-effects input.wav --room-size 0.8 --wet 0.4 --output-path output.wav
```

### Merge audio files

```bash
python cli.py merge \
  --vocals vocals.flac \
  --instrumental instrumental.flac \
  --backing-vocals backing.flac \
  --format mp3
```

## Module Overview

### `main/uvr/` — Audio Separation
Handles all audio source separation tasks using state-of-the-art deep learning models including Mel-Roformer, BS-Roformer, MDX23C, Demucs v4, Bandit-Split RNN, and SCNet architectures:
- Vocal/instrumental separation
- Karaoke (lead + backing vocal) separation
- Dereverb processing
- Deecho processing
- Denoise processing
- Model ensembling for improved separation quality

### `main/rvc/` — Voice Conversion
Wraps the Applio RVC inference engine for high-quality voice conversion with support for multiple pitch extractors (CREPE, FCPE, RMVPE), embedder models, and various export formats. The engine includes a full pipeline architecture with attention-based generators, discriminators, and synthesizer modules.

### `main/tts/` — Text-to-Speech
Microsoft Edge TTS integration with 400+ voices across 11 languages, with optional RVC voice conversion on the generated audio for creating AI covers from text input alone.

### `main/acestep_inference.py` — ACE-Step 1.5 Music Generation
Open-source text-to-music generation powered by the [ACE-Step 1.5](https://github.com/ACE-Step/ACE-Step-1.5) foundation model from ACE Studio & StepFun. Uses a hybrid two-brain architecture: a **5Hz LM planner** that infers BPM, key, lyrics, and semantic audio codes, paired with a **DiT (Diffusion Transformer) executor** that generates audio via flow-matching diffusion. Supports four generation modes:
- **Simple Mode** — Describe music in natural language; the LM auto-generates caption, lyrics, and metadata
- **Custom Mode** — Full manual control over caption, lyrics, BPM, key scale, time signature
- **Cover Mode** — Style-transfer/re-style an existing audio file
- **Repaint Mode** — Regenerate a specific segment of audio

Models auto-download from HuggingFace on first use. See `tabs/acestep_tab.py` for the full UI, or `main/tools/variables.py` for centralized configuration.

### `main/whisper/` — Transcription & Diarization
OpenAI Whisper-based speech-to-text with word-level timestamps, multi-language support, and speaker diarization powered by SpeechBrain and ECAPA-TDNN speaker embeddings. Supports SRT, VTT, and JSON export formats.

### `main/tools/` — Utilities
Shared helpers used across all modules:
- **variables**: Model definitions, FP16 hardware detection, ACE-Step configuration & defaults
- **config**: Application configuration management
- **file_utils**: File search, model metadata lookup, file downloads
- **audio_utils**: Reverb effects (Pedalboard), audio merging (pydub), FP16 config patching
- **downloader**: RVC model download and YouTube music download orchestration
- **gdown / hf / mediafire**: Platform-specific download handlers

### `main/core.py` — Pipeline Orchestrator
The `full_inference_program()` function coordinates the complete audio processing pipeline by calling into the specialized sub-modules in sequence: vocal separation → karaoke separation → dereverb → deecho → denoise → RVC conversion → backing vocals → reverb → pitch adjust → merge.

## Cloud Usage

## Credits

<div align="center">

### 👑 Project Team

| Role | Member | Description |
|:---:|:---:|:---|
| 👑 Base Project Owner | [ShiromiyaG](https://github.com/ShiromiyaG) | Owner of [RVC-AI-Cover-Maker-UI](https://github.com/Eddycrack864/RVC-AI-Cover-Maker-UI) which this project is based on |
| 🔧 Base Project Contributor | [Eddycrack864](https://github.com/Eddycrack864) | Contributor to [RVC-AI-Cover-Maker-UI](https://github.com/Eddycrack864/RVC-AI-Cover-Maker-UI) |
| 🧩 Fork Owner | [BF667](https://github.com/BF667) | Hyper RVC fork owner & maintainer |
| 🧪 Colab UI | [Nick088](https://linktr.ee/Nick088) | Start UI cells in Colab & Kaggle, local setup guide |
| 🧪 QA Testing | [FullmatheusBallZ](https://www.youtube.com/@FullmatheusBallZ) | Google Colab testing & quality assurance |

</div>

---

### 🏗️ Core Projects & Libraries

| Project | Author | Role |
|:---|:---|:---|
| [![RVC-AI-Cover-Maker-UI](https://img.shields.io/badge/RVC_AI_Cover_Maker_UI-6366f1?style=flat-square)](https://github.com/Eddycrack864/RVC-AI-Cover-Maker-UI) | [ShiromiyaG](https://github.com/ShiromiyaG) | Original UI framework & cover pipeline design (owned by ShiromiyaG) |
| [![Applio](https://img.shields.io/badge/Applio-2ea043?style=flat-square)](https://github.com/IAHispano/Applio) | [IAHispano](https://github.com/IAHispano) | RVC inference engine, pitch extraction & model management |
| [![Audio Separator](https://img.shields.io/badge/Audio_Separator-e74c3c?style=flat-square)](https://github.com/karaokenerds/python-audio-separator) | [beveradb](https://github.com/beveradb) | Python audio source separation wrapping UVR models |
| [![UVR GUI](https://img.shields.io/badge/Ultimate_Vocal_Remover-f1c40f?style=flat-square)](https://github.com/Anjok07/ultimatevocalremovergui) | [Anjok07](https://github.com/Anjok07) | Gold standard vocal removal with pretrained model weights |
| [![ZFTurbo](https://img.shields.io/badge/Music_Separation_Training-9b59b6?style=flat-square)](https://github.com/ZFTurbo/Music-Source-Separation-Training) | [ZFTurbo](https://github.com/ZFTurbo) | BS-Roformer, Mel-Band-Roformer, SCNet, MDX23C, Bandit, Demucs |
| [![AICoverGen](https://img.shields.io/badge/AICoverGen-3498db?style=flat-square)](https://github.com/SociallyIneptWeeb/AICoverGen) | [SociallyIneptWeeb](https://github.com/SociallyIneptWeeb) | AI cover generation pipeline & processing concepts |
| [![Vietnamese-RVC](https://img.shields.io/badge/Vietnamese_RVC-16a34a?style=flat-square)](https://github.com/PhamHuynhAnh16/Vietnamese-RVC) | [PhamHuynhAnh16](https://github.com/PhamHuynhAnh16) | Base RVC library code, additional F0 predictors & method fixes |
| [![ACE-Step 1.5](https://img.shields.io/badge/ACE_Step_1.5-f1c40f?style=flat-square)](https://github.com/ACE-Step/ACE-Step-1.5) | [ACE Studio & StepFun](https://github.com/ACE-Step) | Open-source text-to-music foundation model (MIT) |

### 🧠 AI Models & Frameworks

| Library | Author | Purpose |
|:---|:---|:---|
| [![Whisper](https://img.shields.io/badge/Whisper-2ea043?style=flat-square&logo=openai)](https://github.com/openai/whisper) | [OpenAI](https://github.com/openai) | Speech recognition & transcription |
| [![SpeechBrain](https://img.shields.io/badge/SpeechBrain-3498db?style=flat-square)](https://github.com/speechbrain/speechbrain) | SpeechBrain Team | Speaker diarization & ECAPA-TDNN embeddings |
| [![PyTorch](https://img.shields.io/badge/PyTorch-ee4c2c?style=flat-square&logo=pytorch)](https://pytorch.org/) | [Meta AI](https://github.com/pytorch) | Deep learning framework for all neural networks |
| [![Transformers](https://img.shields.io/badge/Transformers-ff9800?style=flat-square&logo=huggingface)](https://github.com/huggingface/transformers) | [HuggingFace](https://github.com/huggingface) | Model loading & pretrained model utilities |
| [![ACE-Step](https://img.shields.io/badge/ACE_Step-f1c40f?style=flat-square)](https://huggingface.co/ACE-Step) | [ACE-Step](https://github.com/ACE-Step) | Music generation: DiT diffusion + 5Hz LM planning |
| [![NumPy](https://img.shields.io/badge/NumPy-013243?style=flat-square&logo=numpy)](https://numpy.org/) | NumPy Team | Numerical computing & array operations |
| [![ONNX Runtime](https://img.shields.io/badge/ONNX_Runtime-5c2d91?style=flat-square)](https://github.com/microsoft/onnxruntime) | [Microsoft](https://github.com/microsoft) | High-performance model inference |

### 🎵 Voice & Pitch Extraction

| Library | Author | Purpose |
|:---|:---|:---|
| [![Edge TTS](https://img.shields.io/badge/Edge_TTS-6366f1?style=flat-square)](https://github.com/rany2/edge-tts) | [rany2](https://github.com/rany2) | 400+ voices in 11 languages via Microsoft Edge |
| [![CREPE](https://img.shields.io/badge/CREPE-2ea043?style=flat-square)](https://github.com/maxrmorrison/crepe) | [Max Morrison](https://github.com/maxrmorrison) | Neural pitch estimation (F0 extraction) |
| [![RMVPE](https://img.shields.io/badge/RMVPE-e74c3c?style=flat-square)](https://github.com/openvpi/RMVPE) | [OpenVPI](https://github.com/openvpi) | Robust vocal pitch estimation |
| [![FCPE](https://img.shields.io/badge/FCPE-f1c40f?style=flat-square)](https://github.com/SCToolsystem/FCPE) | [SCToolsystem](https://github.com/SCToolsystem) | Fundamental frequency contour extraction |
| [![Faiss](https://img.shields.io/badge/Faiss-3498db?style=flat-square)](https://github.com/facebookresearch/faiss) | [Meta Research](https://github.com/facebookresearch) | Voice embedding similarity search & retrieval |
| [![TorchCREPE](https://img.shields.io/badge/TorchCREPE-9b59b6?style=flat-square)](https://github.com/maxrmorrison/crepe-torch) | [Max Morrison](https://github.com/maxrmorrison) | PyTorch-native CREPE implementation |

### 🎧 Audio Processing

| Library | Author | Purpose |
|:---|:---|:---|
| [![Pedalboard](https://img.shields.io/badge/Pedalboard-2ea043?style=flat-square&logo=spotify)](https://github.com/spotify/pedalboard) | [Spotify](https://github.com/spotify) | Studio-quality reverb, EQ & audio effects |
| [![pydub](https://img.shields.io/badge/pydub-e74c3c?style=flat-square)](https://github.com/jiaaro/pydub) | [James Robert](https://github.com/jiaaro) | Audio manipulation, format conversion & merging |
| [![librosa](https://img.shields.io/badge/librosa-f1c40f?style=flat-square)](https://github.com/librosa/librosa) | librosa Team | Music & audio analysis, feature extraction |
| [![ffmpeg](https://img.shields.io/badge/ffmpeg-007808?style=flat-square&logo=ffmpeg)](https://ffmpeg.org/) | FFmpeg Project | Audio/video encoding, decoding & processing |
| [![SoundFile](https://img.shields.io/badge/SoundFile-3498db?style=flat-square)](https://github.com/bastibe/python-soundfile) | Bastian Bechtold | Audio file I/O via libsndfile |
| [![SciPy](https://img.shields.io/badge/SciPy-013243?style=flat-square)](https://scipy.org/) | SciPy Team | Signal processing & scientific computing |

### 📥 Download & Network

| Library | Author | Purpose |
|:---|:---|:---|
| [![yt-dlp](https://img.shields.io/badge/yt--dlp-e74c3c?style=flat-square)](https://github.com/yt-dlp/yt-dlp) | yt-dlp contributors | YouTube & 1000+ site audio/video downloader |
| [![HuggingFace Hub](https://img.shields.io/badge/HuggingFace_Hub-ff9800?style=flat-square&logo=huggingface)](https://github.com/huggingface/huggingface_hub) | [HuggingFace](https://github.com/huggingface) | Model & dataset hosting for pretrained RVC models |
| [![gdown](https://img.shields.io/badge/gdown-6366f1?style=flat-square)](https://github.com/wkentaro/gdown) | [Kentaro Wada](https://github.com/wkentaro) | Google Drive file downloader |
| [![Requests](https://img.shields.io/badge/Requests-2ea043?style=flat-square)](https://github.com/psf/requests) | Kenneth Reitz | HTTP library for Python |
| [![tqdm](https://img.shields.io/badge/tqdm-9b59b6?style=flat-square)](https://github.com/tqdm/tqdm) | Casper da Costa-Luis | Progress bars for downloads & processing |

### 🖼️ UI & Design

| Library | Author | Purpose |
|:---|:---|:---|
| [![Gradio](https://img.shields.io/badge/Gradio-f1c40f?style=flat-square&logo=huggingface)](https://github.com/gradio-app/gradio) | [HuggingFace](https://github.com/gradio-app) | Web UI framework with tabs, sliders & file uploads |
| [![Python](https://img.shields.io/badge/Python_3.12+-3776ab?style=flat-square&logo=python)](https://www.python.org/) | Python Software Foundation | Core language runtime |
| [![Freepik](https://img.shields.io/badge/Freepik-e74c3c?style=flat-square)](https://www.freepik.com) | Freepik | Cyber-themed cover image for the WebUI |

---

<div align="center">

Built with ❤️ by the Hyper-RVC community · Open Source under [MIT License](./LICENSE)

</div>
