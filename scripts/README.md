# TTS Pipeline Scripts

Production-ready tools for audiobook creation with Qwen3-TTS.

## Quick Start

```bash
# Install dependencies
pip install -r ../requirements.txt

# Test the pipeline (no GPU required for import tests)
python tests/test_pipeline.py --no-tts

# Full test with TTS generation (requires GPU)
python tests/test_pipeline.py
```

## Scripts

### tts_generator.py

Core Qwen3-TTS wrapper supporting voice cloning and voice design.

```bash
# Voice design from persona
python tts_generator.py \
    --persona ../personas/examples/narrator-childrens.json \
    --text "Luna was the smallest cloud in the whole wide sky." \
    --output luna_test.wav

# Voice cloning with reference audio
python tts_generator.py \
    --ref-audio reference.wav \
    --ref-text "This is the reference transcript." \
    --text "Text to generate" \
    --output output.wav

# From text file
python tts_generator.py \
    --persona ../personas/examples/narrator-literary.json \
    --text-file chapter.txt \
    --output Chapter_01.wav
```

### acx_validator.py

Validate audio files against ACX/Audible specifications.

```bash
# Validate single file
python acx_validator.py output.wav

# Validate directory
python acx_validator.py audiobook_chapters/

# JSON output
python acx_validator.py output.wav --json

# Strict mode (warnings become failures)
python acx_validator.py output.wav --strict
```

**ACX Requirements Checked:**
- RMS levels: -23 to -18 dB
- Peak levels: -3 dB maximum
- Noise floor: -60 dB maximum
- Sample rate: 44.1 kHz
- Format: 192 kbps CBR MP3
- Room tone: 0.5-1s start, up to 5s end

### manuscript_to_chapters.py

Split manuscripts into chapter files for batch TTS processing.

```bash
# Basic split
python manuscript_to_chapters.py manuscript.txt --output-dir chapters/

# With page-turn pauses (picture books)
python manuscript_to_chapters.py picturebook.txt \
    --page-turns \
    --pause-duration 2.0 \
    --output-dir chapters/

# Generate credits
python manuscript_to_chapters.py manuscript.txt \
    --output-dir chapters/ \
    --author "Jane Smith" \
    --narrator "AI Narrator" \
    --copyright-year 2026

# Dry run (preview without writing)
python manuscript_to_chapters.py manuscript.txt --dry-run
```

## Pipeline Workflow

```
manuscript.txt
      │
      ▼
┌─────────────────────┐
│ manuscript_to_      │
│ chapters.py         │
└─────────────────────┘
      │
      ▼
chapters/
├── manifest.json
├── Book_Chapter_01.txt
├── Book_Chapter_02.txt
└── ...
      │
      ▼
┌─────────────────────┐
│ tts_generator.py    │  ← Uses persona from personas/
└─────────────────────┘
      │
      ▼
audio/
├── Book_Chapter_01.wav
├── Book_Chapter_02.wav
└── ...
      │
      ▼
┌─────────────────────┐
│ acx_validator.py    │
└─────────────────────┘
      │
      ▼
✓ ACX-compliant audiobook
```

## Batch Processing Example

```python
#!/usr/bin/env python3
"""Process entire audiobook from manuscript."""

import json
from pathlib import Path
from tts_generator import Persona, generate_from_persona, save_audio
from acx_validator import validate_audio

# Load manifest
with open("chapters/manifest.json") as f:
    manifest = json.load(f)

# Load persona
persona = Persona.from_json("../personas/examples/narrator-literary.json")

# Process each chapter
for chapter in manifest["chapters"]:
    text_path = Path("chapters") / chapter["text_file"]
    audio_path = Path("audio") / chapter["audio_file"]

    # Read text
    with open(text_path) as f:
        text = f.read()

    # Generate audio
    print(f"Generating: {chapter['title']}")
    wavs, sr = generate_from_persona(text, persona)
    save_audio(wavs, sr, str(audio_path))

    # Validate
    report = validate_audio(str(audio_path))
    if not report.passed:
        print(f"  Warning: {audio_path} needs post-processing")
```

## Hardware Requirements

- **GPU**: 5-10 GB VRAM for 1.7B model (RTX 3090 class recommended)
- **CPU-only**: Use 0.6B model with `--model 0.6B` flag
- **Memory**: 16 GB RAM minimum

## Troubleshooting

**"No module named 'qwen_tts'"**
```bash
pip install qwen-tts
```

**"CUDA out of memory"**
```bash
# Use smaller model
python tts_generator.py --model 0.6B ...
```

**"Noise floor too high"**
- This is expected for TTS output—apply noise reduction in post-processing
- Use a dedicated DAW or ffmpeg for final mastering

**ACX validation failures**
- RMS too quiet: Normalize audio to -20 dB RMS
- Peaks over -3 dB: Apply limiter at -3 dB
- Missing room tone: Add 0.5s silence at start/end
