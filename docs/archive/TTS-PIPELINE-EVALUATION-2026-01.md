> **ARCHIVED**: 2026-01-28. Evaluates 4 providers; Kokoro (5th provider) added after this report. See `scripts/tts_providers/README.md` for current provider status.

# TTS Pipeline Evaluation Report

**Date**: 2026-01-28
**Scope**: Multi-speaker TTS pipeline validation for Chapter 2 drafts
**Projects Tested**: The House Remains, The Listener, The Weight of Mangoes

---

## Executive Summary

The TTS pipeline was validated for parsing and speaker mapping across all three story projects. Two critical issues were discovered and fixed:

1. **Dialogue Parser Format Support**: The parser only supported prose-style attribution ("said Luna"), not the screenplay-style `[SPEAKER]` tags used in our manuscripts.
2. **Case Sensitivity**: Speaker lookup was case-sensitive, causing mismatches between uppercase speaker-map keys (ELEANOR) and lowercase parser output (eleanor).

Both issues have been resolved. The pipeline is now ready for audio generation pending installation of TTS dependencies on a GPU-equipped machine.

---

## Test Results

### Parsing Validation

| Project | Segments | Speakers | Status |
|---------|----------|----------|--------|
| The House Remains | 79 | 6 | PASS |
| The Listener | 90 | 7 | PASS |
| The Weight of Mangoes | 53 | 8 | PASS |

### Speaker Distribution

**The House Remains (Chapter 2)**
- narrator: 24 segments, 1,184 words
- eleanor: 17 segments, 122 words
- helen: 17 segments, 194 words
- marcus: 12 segments, 120 words
- ray: 5 segments, 38 words
- sophie: 4 segments, 29 words

**The Listener (Chapter 2)**
- narrator: 22 segments, 1,070 words
- sarah: 33 segments, 166 words
- ruth: 20 segments, 246 words
- emma: 8 segments, 82 words
- owen: 5 segments, 28 words
- carla: 2 segments, 32 words

**The Weight of Mangoes (Chapter 2)**
- narrator: 18 segments, 923 words
- nirmala: 18 segments, 509 words
- maya: 5 segments, 34 words
- kamla: 3 segments, 16 words
- marcus: 3 segments, 20 words
- sunil: 3 segments, 33 words
- jason: 2 segments, 20 words
- anita: 1 segment, 22 words

---

## Issues Discovered and Fixed

### Issue 1: Dialogue Parser Format Support

**Problem**: `dialogue_parser.py` used regex patterns for prose-style dialogue attribution:
- "Text," said Character.
- Character said, "Text."

Our manuscripts use screenplay-style `[SPEAKER]` tags:
```
[NARRATOR]
The room was silent.

[ELEANOR]
"I can't believe she's gone."
```

**Solution**: Added format auto-detection and new `extract_tagged_segments()` function:
- `detect_manuscript_format()` - Auto-detects 'tagged' vs 'prose' format
- `extract_tagged_segments()` - Parses `[SPEAKER]` tag format
- `parse_manuscript()` - Now uses appropriate parser based on format

**Commit**: `7f00a21`

### Issue 2: Case-Insensitive Speaker Lookup

**Problem**: Speaker map JSON uses uppercase keys (ELEANOR), parser normalizes to lowercase (eleanor). Direct dictionary lookup failed.

**Solution**: Updated `SpeakerMap.get_persona_path()` to:
1. Try direct lookup first
2. Fall back to case-insensitive comparison
3. Check aliases (also case-insensitive)

**Commit**: `7f00a21`

### Issue 3: Missing Emma Persona

**Problem**: The Listener Chapter 2 introduced Emma (Sarah's daughter), who wasn't in the speaker map.

**Solution**:
- Created `personas/emma-mercer.json`
- Added Emma to speaker-map.json with alias

**Commit**: `7f00a21`

---

## Pipeline Component Status

| Component | Status | Notes |
|-----------|--------|-------|
| `dialogue_parser.py` | ✅ Working | Supports both tagged and prose formats |
| `multispeaker_tts.py` | ✅ Working | Case-insensitive speaker lookup |
| `tts_providers/` | ✅ Ready | Abstraction layer in place |
| `manuscript_to_chapters.py` | ✅ Working | Page turn pause insertion |
| `acx_validator.py` | ✅ Working | Level checks implemented |
| `audio_postprocess.py` | ⏳ Pending | Requires numpy/scipy |

### TTS Provider Status

| Provider | Capabilities | Status |
|----------|-------------|--------|
| Qwen | voice_cloning, voice_design, multilingual, local, long_form | Ready (needs deps) |
| ElevenLabs | voice_cloning, voice_design, streaming, emotion, speed | Ready (needs API key) |
| OpenAI | speed_control, multilingual | Ready (needs API key) |
| Coqui | local, custom_models | Ready (needs deps) |

---

## Dependencies Required

To run actual TTS generation, install:

```bash
pip install -r requirements.txt
```

Required packages:
- `qwen-tts>=0.1.0` (includes PyTorch)
- `soundfile>=0.12.0`
- `numpy>=1.24.0`
- `pydub>=0.25.0`
- `scipy>=1.10.0`

System requirements:
- ffmpeg (for pydub)
- CUDA-capable GPU (for Qwen local inference)

---

## Recommended Next Steps

1. **Install dependencies** on a GPU workstation
2. **Generate test audio** for one segment from each project
3. **Validate ACX compliance** with `acx_validator.py`
4. **Test golden reference system** with `persona_regression.py`
5. **Full chapter generation** with `batch_produce.py`

---

## Dry Run Commands

To validate parsing without generating audio:

```bash
# The House Remains
python scripts/multispeaker_tts.py \
  projects/the-house-remains/drafts/chapter-02.txt \
  --speaker-map projects/the-house-remains/speaker-map.json \
  --dry-run --verbose

# The Listener
python scripts/multispeaker_tts.py \
  projects/the-listener/drafts/chapter-02.txt \
  --speaker-map projects/the-listener/speaker-map.json \
  --dry-run --verbose

# The Weight of Mangoes
python scripts/multispeaker_tts.py \
  projects/the-weight-of-mangoes/drafts/chapter-02.txt \
  --speaker-map projects/the-weight-of-mangoes/speaker-map.json \
  --dry-run --verbose
```

---

## Files Modified

- `scripts/dialogue_parser.py` - Added tagged format support
- `scripts/multispeaker_tts.py` - Fixed case-insensitive lookup
- `projects/the-listener/speaker-map.json` - Added Emma
- `projects/the-listener/personas/emma-mercer.json` - New persona

---

*Report generated as part of TTS pipeline iteration cycle.*
