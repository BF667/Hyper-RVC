# TTS Inference Feature

## Overview

Hyper-RVC now includes a comprehensive Text-to-Speech (TTS) inference feature powered by **Microsoft Azure's Edge TTS** with optional **RVC voice conversion** integration.

## Features

### 🎤 Edge TTS (Microsoft Azure)
- **400+ Natural Neural Voices** across 100+ languages
- **High-Quality Speech Synthesis** using Azure's neural TTS
- **Free to Use** - No API key required
- **Multiple Languages** - Support for major world languages
- **Adjustable Speech Rate** - From -30% to +30% speed

### 🎯 RVC Voice Conversion
- **Convert TTS to Any Voice** - Use your favorite RVC models
- **Customizable Parameters** - Pitch, filter radius, index rate, etc.
- **Real-time Voice Transformation** - Azure quality + custom voices
- **Optional Feature** - Use TTS alone or with RVC

## Available Voices by Language

### English (US)
- Jenny, Guy, Aria, Davis, Amber, Ana, Ashley, Brandon, Christopher, Cora, Elizabeth, Eric, Jacob, Michelle, Monica, Roger

### English (UK)
- Sonia, Ryan, Libby, Abbi, Alfie, Bella, Elliot, Ethan, Hollie, Maisie, Noah, Oliver, Olivia, Thomas

### Spanish
- Elvira, Alvaro (Spain)
- Dalia, Jorge (Mexico)
- Elena, Tomas (Argentina)
- Salome, Gonzalo (Colombia)

### French
- Denise, Henri (France)
- Sylvie, Jean, Antoine (Canada)

### German
- Katja, Conrad, Amala, Bernd, Christoph, Elke, Gisela, Kasper, Killian, Klarissa, Klaus, Louisa, Maja, Ralf, Tanja

### Portuguese (Brazil)
- Francisca, Antonio, Brenda, Donato, Elza, Fabio, Giovanna, Humberto, Julio, Leila, Leticia, Manuela, Nicolau, Valerio, Yara

### Italian
- Elsa, Diego, Benigno, Calimero, Cataldo, Fabiola, Fiamma, Gianni, Imma, Irma, Lisandro, Palmira, Pierina, Rinaldo

### Japanese
- Nanami, Keita, Aoi, Daichi, Mayu, Naoki, Shiori

### Korean
- SunHi, InJoon, BongJin, GookMin, JiMin, SeoHyeon, SoonBok, YuJin

### Chinese (Mandarin)
- Xiaoxiao, Yunxi, Yunyang, Xiaoyi, Yunjian, Xiaochen, Xiaohan, Xiaomeng, Xiaomo, Xiaoqiu, Xiaorui, Xiaoshuang, Xiaoxuan, Xiaoyan, Xiaoyou, Xiaozhen, Yunfeng, Yunhao, Yunxia, Yunye, Yunze

### Other Languages
- Russian: Svetlana, Dmitry
- Arabic: Zariyah, Hamed
- Hindi: Swara, Madhur

## Usage

### Web UI

1. **Open Hyper-RVC WebUI**
2. Navigate to **"TTS Inference"** tab
3. **Enter Text** - Type or paste your text (max 5000 characters)
4. **Select Voice** - Choose language and voice
5. **Adjust Rate** - Set speech speed
6. **Optional: Enable RVC** - Convert with RVC model
7. Click **"🎯 Generate TTS"**

### Two-Stage Process

#### Stage 1: TTS Generation
- Converts text to speech using Azure voices
- Generates high-quality neural TTS audio
- Saved as WAV format

#### Stage 2: RVC Conversion (Optional)
- Takes TTS output as input
- Applies voice conversion model
- Transforms to target voice
- Exports in selected format

## Output Formats

- **WAV** - Uncompressed, highest quality
- **MP3** - Compressed, universal compatibility
- **FLAC** - Lossless compression
- **OGG** - Open source format
- **M4A** - Apple format

## RVC Parameters

When using RVC voice conversion:

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| **Pitch** | -12 to +12 | 0 | Semitone adjustment |
| **Filter Radius** | 0-7 | 3 | Median filtering |
| **Index Rate** | 0-1 | 0.75 | Voice similarity |
| **RMS Mix Rate** | 0-1 | 0.25 | Volume envelope |
| **Protect** | 0-0.5 | 0.33 | Consonant protection |

## Examples

### Basic TTS (No RVC)
```
Text: "Hello, welcome to Hyper-RVC!"
Language: English (US)
Voice: en-US-JennyNeural
Rate: Normal (0%)
Result: High-quality TTS with Azure voice
```

### TTS + RVC Conversion
```
Text: "This is a custom voice!"
Language: English (US)
Voice: en-US-JennyNeural
RVC: Enabled
Model: your_voice_model.pth
Pitch: +2 (slightly higher)
Index Rate: 0.8 (strong voice match)
Result: Azure quality with custom voice characteristics
```

### Adjusting Speech Rate
```
Slow (-20%): Better clarity, dramatic effect
Normal (0%): Natural pacing
Fast (+20%): Quick delivery, energetic
```

## Tips for Best Results

### Text Preparation
1. **Use Punctuation** - Commas, periods for natural pauses
2. **Break Long Texts** - Split into paragraphs
3. **Check Spelling** - Affects pronunciation
4. **Avoid Special Characters** - May cause issues

### Voice Selection
1. **Match Content** - Formal vs casual voices
2. **Test Different Voices** - Each has unique characteristics
3. **Consider Audience** - Language and accent

### RVC Conversion
1. **Start Conservative** - Index rate 0.6-0.8
2. **Adjust Pitch Carefully** - ±2 semitones max initially
3. **Use Quality Models** - Well-trained RVC models
4. **Test Short Samples** - Before processing long texts

## Use Cases

### Content Creation
- YouTube video narration
- Podcast introductions
- Audiobook production
- E-learning content

### Character Voices
- Game character dialogue
- Animation voiceovers
- Virtual assistant personas
- Role-playing content

### Accessibility
- Text-to-speech for visually impaired
- Reading assistance
- Language learning

### Prototyping
- Voice-over drafts
- Script read-throughs
- Timing tests

## Technical Details

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | Dual-core | Quad-core+ |
| **RAM** | 4GB | 8GB+ |
| **GPU** | Optional | CUDA-capable |
| **VRAM** | N/A | 4GB+ for RVC |
| **Storage** | 1GB free | 5GB+ free |

### Performance

**TTS Generation:**
- Real-time factor: 0.1-0.3x (faster than realtime)
- No GPU required
- Network connection needed for Edge TTS

**RVC Conversion:**
- Real-time factor: 0.5-2x (depends on model)
- GPU recommended for speed
- Runs locally

### File Locations

- **TTS Output:** `audio_files/tts_output/`
- **RVC Output:** `audio_files/tts_output/`
- **Models:** `logs/` directory

## Troubleshooting

### Common Issues

**"TTS generation failed"**
- Check internet connection (Edge TTS requires online)
- Verify text is not empty
- Try different voice

**"RVC model not found"**
- Ensure model file exists in logs/
- Refresh model list
- Check file path

**Audio Quality Issues**
- Increase index rate for better voice match
- Adjust pitch if too high/low
- Use higher quality export format (WAV/FLAC)

**Slow Processing**
- Enable GPU acceleration
- Use smaller RVC models
- Reduce audio length

**Character Limit**
- Maximum 5000 characters per generation
- Split longer texts into multiple parts
- Generate in batches

## Advanced Usage

### Batch Processing
Process multiple text segments:
1. Generate TTS for each segment
2. Apply same RVC settings
3. Merge audio files externally

### Voice Blending
Create unique voices:
1. Generate TTS with Azure voice
2. Apply RVC with low index rate (0.3-0.5)
3. Blend characteristics of both voices

### Pitch Correction
Fix pitch issues:
1. Generate TTS at normal rate
2. Apply RVC with pitch adjustment
3. Fine-tune in post-processing

## Integration with Other Features

### Whisper + TTS
- Transcribe audio with Whisper
- Use transcription as TTS input
- Generate new voice-over

### TTS + Full Inference
- Generate TTS audio
- Use in Full Inference tab
- Apply additional processing

## API Usage

### Programmatic Access

```python
from tabs.tts_inference import run_tts_inference

# Generate TTS only
status, tts_path, _ = run_tts_inference(
    text="Hello World!",
    language="English (US)",
    voice="en-US-JennyNeural",
    rate=0,
    use_rvc=False,
    model_path="",
    index_path="",
    pitch=0,
    pitch_extract="rmvpe",
    filter_radius=3,
    index_rate=0.75,
    rms_mix_rate=0.25,
    protect=0.33,
    embedder_model="contentvec",
    devices="0",
    export_format="WAV"
)

# Generate TTS + RVC
status, tts_path, rvc_path = run_tts_inference(
    text="Hello World!",
    language="English (US)",
    voice="en-US-JennyNeural",
    rate=0,
    use_rvc=True,
    model_path="logs/model.pth",
    index_path="logs/model.index",
    pitch=2,
    pitch_extract="rmvpe",
    filter_radius=3,
    index_rate=0.8,
    rms_mix_rate=0.25,
    protect=0.33,
    embedder_model="contentvec",
    devices="0",
    export_format="WAV"
)
```

## Credits

- **Edge TTS**: Microsoft Azure
- **RVC**: RVC Project Team
- **Hyper-RVC**: Hyper-RVC Development Team

## Resources

- [Edge TTS GitHub](https://github.com/rany2/edge-tts)
- [Azure TTS Documentation](https://azure.microsoft.com/en-us/products/cognitive-services/text-to-speech/)
- [RVC Documentation](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI)
- [Hyper-RVC README](../README.md)
