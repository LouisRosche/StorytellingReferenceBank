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

### audio_postprocess.py

ACX-compliant mastering chain for raw TTS output.

```bash
# Process single file
python audio_postprocess.py raw_audio.wav --output mastered.mp3

# Process directory
python audio_postprocess.py raw_chapters/ --output-dir mastered/

# Analyze without processing
python audio_postprocess.py audio.wav --analyze

# Custom parameters
python audio_postprocess.py raw.wav -o final.mp3 \
    --target-rms -20 --limiter-ceiling -3 \
    --room-tone-head 0.5 --room-tone-tail 3.0
```

**Processing Chain:**
1. High-pass filter (80 Hz) - removes rumble
2. Low-pass filter (16 kHz) - removes hiss
3. Compression (2.5:1, -24 dB threshold, soft knee)
4. De-essing (4-8 kHz band)
5. Limiter (-3 dB ceiling)
6. Loudness normalization (-20 dB RMS)
7. Room tone insertion (0.5s head, 3s tail)
8. Export: 192 kbps CBR MP3, 44.1 kHz, mono

### batch_produce.py

Full pipeline orchestrator: manuscript → distributable audiobook.

```bash
# Full production (requires GPU)
python batch_produce.py manuscript.txt \
    --persona ../personas/examples/narrator-literary.json \
    --output-dir audiobook/ \
    --title "My Book" --author "Jane Doe" --narrator "AI Voice"

# Dry run (test orchestration without TTS)
python batch_produce.py manuscript.txt \
    --persona ../personas/examples/narrator-childrens.json \
    --dry-run --verbose

# Picture book with page-turn pauses
python batch_produce.py picturebook.txt \
    --persona ../personas/examples/narrator-childrens.json \
    --page-turns --pause-duration 2.0 \
    --output-dir audiobook/
```

**Produces:**
- ACX-compliant chapter MP3s
- Opening/closing credits
- Retail sample (first 5 min of chapter 1)
- `production_report.json` with full status

## Pipeline Workflow

```
manuscript.txt + persona.json
           │
           ▼
    ┌──────────────────┐
    │  batch_produce   │  ← Full orchestrator
    └──────────────────┘
           │
           ├─────────────────────────────────────────┐
           │                                         │
           ▼                                         │
    ┌──────────────────┐                             │
    │ manuscript_to_   │  STAGE 1: PREP              │
    │ chapters.py      │                             │
    └──────────────────┘                             │
           │                                         │
           ▼                                         │
    prep/                                            │
    ├── Chapter_01.txt                               │
    ├── Opening_Credits.txt                          │
    └── manifest.json                                │
           │                                         │
           ▼                                         │
    ┌──────────────────┐                             │
    │ tts_generator.py │  STAGE 2: TTS               │
    └──────────────────┘                             │
           │                                         │
           ▼                                         │
    raw_audio/                                       │
    ├── Chapter_01.wav                               │
    └── Opening_Credits.wav                          │
           │                                         │
           ▼                                         │
    ┌──────────────────┐                             │
    │ audio_postprocess│  STAGE 3: MASTER            │
    └──────────────────┘                             │
           │                                         │
           ▼                                         │
    final/                                           │
    ├── Chapter_01.mp3  (ACX-compliant)              │
    ├── Opening_Credits.mp3                          │
    └── Retail_Sample.mp3                            │
           │                                         │
           ▼                                         │
    ┌──────────────────┐                             │
    │ acx_validator.py │  STAGE 4: VALIDATE          │
    └──────────────────┘                             │
           │                                         │
           ▼                                         │
    production_report.json ◄─────────────────────────┘
           │
           ▼
    ✓ Distributable audiobook
```

## Batch Processing

The recommended approach is to use `batch_produce.py` which orchestrates the full pipeline:

```bash
# Complete audiobook production
python batch_produce.py my_novel.txt \
    --persona ../personas/examples/narrator-literary.json \
    --title "My Novel" \
    --author "Jane Doe" \
    --narrator "AI Narrator" \
    --output-dir my_novel_audiobook/ \
    --verbose
```

For custom workflows, you can chain scripts manually:

```bash
# Step 1: Split manuscript
python manuscript_to_chapters.py novel.txt -o chapters/

# Step 2: Generate TTS for each chapter
for f in chapters/*.txt; do
    python tts_generator.py --persona ../personas/examples/narrator-literary.json \
        --text-file "$f" --output "raw_audio/$(basename ${f%.txt}).wav"
done

# Step 3: Post-process for ACX compliance
python audio_postprocess.py raw_audio/ --output-dir final/

# Step 4: Validate
python acx_validator.py final/
```

## Hardware Requirements

- **GPU**: 5-10 GB VRAM for 1.7B model (RTX 3090 class recommended)
- **CPU-only**: Use 0.6B model with `--model 0.6B` flag
- **Memory**: 16 GB RAM minimum

## Bespoke Personalities Tools

### persona_compatibility.py

Story-to-persona matching for the bespoke reading personalities product.

```bash
# Score all personas against a story
python persona_compatibility.py --story story.json --top 5

# Score specific persona
python persona_compatibility.py --story story.json --persona narrator-literary-female

# JSON output
python persona_compatibility.py --story story.json --json
```

**Story JSON format:**
```json
{
  "genre": "literary fiction",
  "tone": ["contemplative", "melancholic"],
  "audience": "adult",
  "language": "en"
}
```

### persona_regression.py

Regression testing for persona voice consistency.

```bash
# Run all regression tests
python persona_regression.py

# Test specific personas
python persona_regression.py --personas narrator-literary-female narrator-thriller

# Custom threshold
python persona_regression.py --threshold 0.90

# JSON output for CI
python persona_regression.py --json
```

Compares generated audio against golden references using MFCC fingerprints. Threshold: 0.85 cosine similarity.

---

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
- This is expected for raw TTS output
- Run `audio_postprocess.py` to apply full mastering chain

**ACX validation failures**
- Run `audio_postprocess.py` on raw files - it handles all ACX requirements:
  - Normalizes to -20 dB RMS (center of -23 to -18 range)
  - Limits peaks to -3 dB
  - Adds room tone (0.5s head, 3s tail)
  - Exports as 192 kbps CBR MP3, 44.1 kHz, mono

**"No module named 'scipy'"**
```bash
pip install scipy
```

**ffmpeg errors with pydub**
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```
