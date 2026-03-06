# Getting Started

From clone to first audiobook production run.

---

## Prerequisites

| Requirement | Minimum | Notes |
|-------------|---------|-------|
| Python | 3.10+ | 3.11 or 3.12 recommended |
| ffmpeg | Any recent | Required by pydub for MP3 export |
| GPU | Optional | 8GB+ VRAM for Qwen3-TTS 1.7B model. CPU fallback uses 0.6B model (slower, lower quality) |
| RAM | 16GB | 32GB recommended for long-form production |
| Disk | 10GB free | Model weights + audio output |

### Install ffmpeg

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Verify
ffmpeg -version
```

---

## 1. Clone and Install

```bash
git clone <your-repo-url> StorytellingReferenceBank
cd StorytellingReferenceBank
```

### Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
```

### Install core dependencies

```bash
pip install -r requirements.txt
```

This installs: numpy, soundfile, pydub, scipy. These cover manuscript processing, audio post-processing, and ACX validation — everything except TTS generation itself.

### Install TTS engine (when ready for audio generation)

```bash
# Qwen3-TTS (primary engine, requires GPU)
pip install qwen-tts

# PyTorch with CUDA (if not already installed via qwen-tts)
# See https://pytorch.org/get-started/locally/ for your CUDA version
```

### Install optional tools

```bash
# Web studio interface
pip install gradio

# Development/testing
pip install pytest

# Voice regression testing (MFCC fingerprinting)
pip install librosa
```

---

## 2. Verify Your Environment

Run the pre-flight checker. This validates dependencies, GPU availability, and project structure.

```bash
# Check dependencies only (no GPU needed)
python scripts/preflight_check.py --deps-only
```

Expected output for a fresh install without TTS:

```
✓ Dependency: numpy          installed
✓ Dependency: soundfile      installed
✓ Dependency: scipy          installed
✓ Dependency: pydub          installed
✗ PyTorch                    not installed
✗ Qwen-TTS                   not installed
✓ ffmpeg                     available
```

PyTorch and Qwen-TTS warnings are expected if you haven't installed the TTS engine yet. Everything else should pass.

### Run the test suite

```bash
# With pytest (if installed)
pytest

# Without pytest
python scripts/tests/test_dialogue_parser.py
python scripts/tests/test_pipeline.py --no-tts
```

The `--no-tts` flag skips GPU-dependent generation tests. The import and parsing tests should all pass.

---

## 3. Understand the Structure

```
templates/structures/     # Story frameworks (Three-Act, Save the Cat, etc.)
templates/characters/     # Character development sheets
templates/worlds/         # World-building framework
templates/series/         # Series bible template
style-guides/             # Genre conventions
references/               # Craft principles
personas/                 # TTS voice library (15 voices)
  examples/               # Persona JSON definitions
  golden/                 # Regression test infrastructure
  schema.json             # Persona file format
audiobook-specs/          # ACX/Audible technical specs
scripts/                  # Production pipeline
  tts_providers/          # Pluggable TTS backends
  tests/                  # Test suite
projects/                 # Active works
docs/                     # Production guides
```

Full file-to-topic lookup: `INDEX.md`

---

## 4. Your First Dry Run

The Luna project is the repo's reference example — a children's picture book with 5 character voices. Use it to verify the pipeline works before creating your own project.

### Inspect the project structure

```bash
ls projects/luna-the-little-cloud/
```

Key files:
- `drafts/` — manuscript files
- `personas/` — project-specific voice definitions
- `speaker-map.json` — maps characters to voice personas
- `story-bible/` — character and world documentation

### Validate the project

```bash
python scripts/preflight_check.py --project luna-the-little-cloud
```

This checks that all persona files exist, speaker-map references resolve, and manuscripts parse correctly.

### Run a dry production

```bash
python scripts/batch_produce.py \
    projects/luna-the-little-cloud/drafts/manuscript-v1-tts.txt \
    --persona projects/luna-the-little-cloud/personas/narrator-luna-warm.json \
    --page-turns \
    --pause-duration 2.0 \
    --dry-run \
    --verbose
```

`--dry-run` runs the full pipeline orchestration (manuscript splitting, chapter planning, file naming, validation report) without calling the TTS engine. No GPU required.

### Inspect a manuscript

```bash
python scripts/inspect_manuscript.py \
    projects/luna-the-little-cloud/drafts/manuscript-v1-tts.txt \
    --speaker-map projects/luna-the-little-cloud/speaker-map.json
```

Reports: segment count, word count, estimated duration, speaker distribution, and any problems.

---

## 5. Full Production Run (Requires GPU + TTS)

Once qwen-tts is installed and a GPU is available:

```bash
python scripts/batch_produce.py \
    projects/luna-the-little-cloud/drafts/manuscript-v1-tts.txt \
    --persona projects/luna-the-little-cloud/personas/narrator-luna-warm.json \
    --title "Luna the Little Cloud" \
    --author "Your Name" \
    --narrator "AI Narrator" \
    --page-turns \
    --pause-duration 2.0 \
    --output-dir output/luna/ \
    --verbose
```

### What this produces

```
output/luna/
├── final/
│   ├── Opening_Credits.mp3       # Title, author, narrator
│   ├── Chapter_01.mp3            # ACX-compliant audio
│   ├── Closing_Credits.mp3
│   └── Retail_Sample.mp3         # First 5 minutes (for store preview)
├── raw_audio/                    # Pre-mastering WAV files
├── prep/                         # Split chapter text + manifest
└── production_report.json        # Full pipeline status
```

### Validate the output

```bash
python scripts/acx_validator.py output/luna/final/
```

Checks every file against ACX specs: RMS levels, peak levels, noise floor, sample rate, format.

---

## 6. Create Your Own Project

### Directory structure

```bash
mkdir -p projects/my-novel/{drafts,story-bible/characters,personas}
```

### Speaker map

Create `projects/my-novel/speaker-map.json`:

```json
{
  "title": "My Novel",
  "default_persona": "personas/narrator.json",
  "speakers": {
    "NARRATOR": {
      "persona_path": "personas/narrator.json",
      "description": "Third-person limited narrator"
    },
    "ALICE": {
      "persona_path": "personas/alice.json",
      "description": "Protagonist, 30s, determined"
    }
  },
  "aliases": {
    "dr. chen": "ALICE"
  },
  "production_notes": {
    "crossfade_ms": 100,
    "dialogue_pause_ms": 200
  }
}
```

### Choose personas

Browse the voice library:

```bash
ls personas/examples/
```

Copy and customize for your project:

```bash
cp personas/examples/narrator-literary.json projects/my-novel/personas/narrator.json
```

Or use the compatibility scorer to find the best match:

```bash
python scripts/persona_compatibility.py \
    --story '{"genre": "literary fiction", "tone": ["contemplative"], "audience": "adult"}' \
    --top 5
```

### Manuscript format

Two formats are auto-detected:

**Tagged** (recommended for multi-speaker):
```
[NARRATOR]
The room was quiet when she entered.

[ALICE]
"Is anyone here?"

[NARRATOR]
No answer came.
```

**Prose** (natural dialogue attribution):
```
The room was quiet when she entered.

"Is anyone here?" Alice called out.

No answer came.
```

### Validate before producing

```bash
python scripts/preflight_check.py --project my-novel
```

---

## 7. Multi-Speaker Production

For manuscripts with multiple character voices:

```bash
# Preview speaker-to-persona mapping
python scripts/multispeaker_tts.py \
    projects/my-novel/drafts/chapter-01.txt \
    --speaker-map projects/my-novel/speaker-map.json \
    --dry-run

# Generate with different voices per character
python scripts/multispeaker_tts.py \
    projects/my-novel/drafts/chapter-01.txt \
    --speaker-map projects/my-novel/speaker-map.json \
    --output chapter-01.wav
```

---

## 8. Web Studio (Optional)

For a browser-based interface:

```bash
pip install gradio
python scripts/web_studio.py
# Access at http://localhost:7860
```

Tabs: Quick Generate, Project Production, Persona Editor, Voice Cloning, Voice Finder.

---

## Pipeline Reference

```
manuscript.txt + persona.json
         │
         ▼
  manuscript_to_chapters.py    → prep/Chapter_*.txt + manifest.json
         │
         ▼
  tts_generator.py             → raw_audio/Chapter_*.wav
         │
         ▼
  audio_postprocess.py         → final/Chapter_*.mp3 (ACX-compliant)
         │
         ▼
  acx_validator.py             → validation report
```

`batch_produce.py` orchestrates all four stages. Run stages individually for custom workflows.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `No module named 'qwen_tts'` | `pip install qwen-tts` |
| `No module named 'scipy'` | `pip install scipy` |
| `CUDA out of memory` | Use `--model 0.6B` for smaller model |
| `ffmpeg not found` | `apt install ffmpeg` or `brew install ffmpeg` |
| ACX validation failures on raw audio | Expected — run `audio_postprocess.py` first |
| Pipeline crash mid-production | Check `production_report.json`, re-run missing chapters manually (see `scripts/README.md` troubleshooting) |

---

## Next Steps

- **Craft resources**: `references/the-craft-of-lasting-work.md`, `references/master-techniques.md`
- **Genre conventions**: `style-guides/genre-guide.md`
- **Revision workflow**: `templates/revision-workflow.md`
- **Commercial production**: `docs/commercial-production-checklist.md`
- **Voice cloning**: `docs/voice-cloning-workflow.md`
- **Sound design**: `audiobook-specs/sound-design-spec.md`
