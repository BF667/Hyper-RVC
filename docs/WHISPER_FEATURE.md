# Whisper Transcription Feature

## Overview

Hyper-RVC now includes built-in Whisper-based speech transcription and speaker diarization capabilities using the Whisper AI model from OpenAI.

## Features

### 🎙️ Speech-to-Text Transcription
- Convert audio to text with high accuracy
- Support for 99+ languages
- Auto language detection
- Word-level timestamps

### 📝 Multiple Output Formats
- **TXT**: Plain text with timestamps
- **JSON**: Structured data with metadata
- **SRT**: Subtitle format for video players
- **VTT**: WebVTT for web video players

### 🚀 Model Options
| Model | Parameters | Speed | Accuracy | Use Case |
|-------|------------|-------|----------|----------|
| Tiny | 39M | Fastest | Good | Quick tests |
| Base | 74M | Fast | Better | Fast transcription |
| Small | 244M | Medium | High | Balanced use |
| Medium | 769M | Slow | Very High | Quality focus |
| Large-v3 | 1550M | Slowest | Best | Production use |

## Usage

### Web UI

1. Open Hyper-RVC WebUI
2. Navigate to **"Whisper Transcription"** tab
3. Upload your audio file
4. Select model size (recommended: `large-v3`)
5. Choose device (CUDA recommended if available)
6. Select language or leave empty for auto-detect
7. Click **"🎯 Transcribe Audio"**

### Programmatic Usage

```python
from tabs.whisper_transcription import run_whisper_transcription

# Run transcription
status, transcription, output_path = run_whisper_transcription(
    audio_path="path/to/audio.wav",
    model_size="large-v3",
    device="cuda",
    language="en",  # Empty string for auto-detect
    word_timestamps=True,
    output_format="txt",
    output_dir="output/transcriptions"
)

print(status)
print(transcription)
```

## Supported Languages

- English (en)
- Chinese (zh)
- German (de)
- Spanish (es)
- Russian (ru)
- Korean (ko)
- French (fr)
- Japanese (ja)
- Portuguese (pt)
- Turkish (tr)
- Polish (pl)
- And 89 more languages!

## Output Examples

### TXT Format
```
[00:00.000 -> 00:03.500] Hello, welcome to Hyper-RVC.
[00:03.500 -> 00:06.000] This is a transcription example.
```

### SRT Format (Subtitles)
```
1
00:00:00,000 --> 00:00:03,500
Hello, welcome to Hyper-RVC.

2
00:00:03,500 --> 00:00:06,000
This is a transcription example.
```

### JSON Format
```json
[
  {
    "start": 0.0,
    "end": 3.5,
    "text": "Hello, welcome to Hyper-RVC.",
    "language": "en"
  }
]
```

## Tips for Best Results

1. **Model Selection**: Use `large-v3` for best accuracy, `base` or `small` for faster results
2. **Audio Quality**: Higher quality audio produces better transcriptions
3. **Language Selection**: Manually select language if auto-detection fails
4. **Word Timestamps**: Enable for precise segmentation (slightly slower)
5. **GPU Acceleration**: Use CUDA device for faster processing

## Hardware Requirements

| Model | VRAM (GPU) | RAM (CPU) | Processing Time* |
|-------|-----------|-----------|------------------|
| Tiny | ~1GB | ~2GB | ~0.1x realtime |
| Base | ~1GB | ~3GB | ~0.2x realtime |
| Small | ~2GB | ~4GB | ~0.5x realtime |
| Medium | ~5GB | ~6GB | ~1x realtime |
| Large-v3 | ~10GB | ~8GB | ~2x realtime |

*Processing time relative to audio duration on RTX 3080

## Troubleshooting

### Out of Memory Error
- Use a smaller model (tiny, base, or small)
- Close other GPU applications
- Use CPU device (slower but works)

### Language Detection Issues
- Manually select the language from dropdown
- Ensure audio has clear speech

### Slow Processing
- Use smaller model
- Enable GPU acceleration (CUDA)
- Reduce audio length (split long files)

## Integration with RVC

The Whisper transcription feature can be used alongside RVC voice conversion:
1. Transcribe audio with Whisper
2. Use transcription to identify segments
3. Apply RVC voice conversion to specific segments
4. Merge converted segments back together

## Credits

- [Whisper by OpenAI](https://github.com/openai/whisper)
- SpeechBrain for speaker diarization components
- Hyper-RVC development team
