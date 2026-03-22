# Voice Cloning Workflow

How to create and use cloned voices for audiobook production.

---

## Overview

Voice cloning creates a TTS voice that mimics a reference recording. Use cases:

- **Author narration**: Clone your own voice to narrate without recording everything
- **Consistent character voice**: Clone a voice actor for a recurring character
- **Historical/archival**: Clone from existing recordings (with rights)
- **Custom brand voice**: Create a signature voice for your catalog

---

## Legal and Ethical Requirements

### You MUST have:

1. **Rights to the voice** — either your own voice, or explicit written permission from the voice owner
2. **Clear intended use** — commercial vs. personal
3. **No deceptive intent** — don't clone to impersonate without consent

### Documentation to maintain:

```
voice-clones/
├── voice-name/
│   ├── reference-audio/
│   │   └── sample-01.wav
│   ├── consent-form.pdf       # If not your own voice
│   ├── rights-documentation.md
│   └── persona.json
```

### Sample consent form elements:

- Voice owner's name and contact
- Scope of permitted use (this project only? all projects? commercial?)
- Duration of permission
- Attribution requirements
- Revocation terms
- Signature and date

---

## Reference Audio Requirements

### Technical Specifications

| Parameter | Requirement | Why |
|-----------|-------------|-----|
| **Duration** | 10-30 seconds optimal | Too short = poor capture; too long = diminishing returns |
| **Format** | WAV or FLAC, uncompressed | MP3 compression loses detail |
| **Sample rate** | 44.1 kHz or higher | Matches production output |
| **Bit depth** | 16-bit or higher | Standard quality |
| **Channels** | Mono preferred | Stereo can confuse models |

### Recording Quality

| Factor | Good | Bad |
|--------|------|-----|
| **Background noise** | Silent room, < -60 dB noise floor | AC hum, traffic, room echo |
| **Microphone** | Consistent distance, pop filter | Plosives, handling noise |
| **Performance** | Natural, representative | Strained, unnatural, reading cold |
| **Content** | Varied sentences, full range | Single phrase repeated |

### What to Record

Record content that demonstrates:

1. **Natural speech patterns** — not stilted reading
2. **Emotional range** — at least neutral and one emotion you'll need
3. **Vocal characteristics** — any distinctive features (breathiness, resonance)
4. **Pronunciation samples** — if there are specific terms in your project

**Example script for 30-second reference:**

> "When I was young, my grandmother used to tell me stories about the old country. She'd sit by the window in the late afternoon light, and her voice would get soft and far away, like she was seeing it all again. I never got tired of listening. Even now, when I close my eyes, I can hear her."

This captures: conversational tone, emotional memory, varied sentence structure, natural pauses.

---

## Cloning Process

### Step 1: Prepare Reference Audio

```bash
# Convert to required format if needed
ffmpeg -i input.mp3 -ar 44100 -ac 1 -acodec pcm_s16le reference.wav

# Check duration
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 reference.wav

# Trim to optimal length if needed (first 30 seconds)
ffmpeg -i reference.wav -t 30 -c copy reference-trimmed.wav
```

### Step 2: Create Persona with Reference

```json
{
  "id": "cloned-author-voice",
  "name": "Author Narration (Cloned)",
  "voice_prompt": "Perfect audio quality. Match the reference voice exactly for timbre and tone. Warm, conversational, slightly literary. Natural pacing with thoughtful pauses.",
  "reference_audio": {
    "path": "voice-clones/author/reference-trimmed.wav",
    "transcript": "The opening passage read naturally by the author.",
    "duration_seconds": 15
  },
  "voice_attributes": {
    "age_range": "40s",
    "gender": "as reference",
    "pitch": "as reference",
    "pace": "natural",
    "texture": "as reference",
    "accent": "as reference",
    "languages": ["en"]
  },
  "emotional_range": ["warm", "reflective", "engaged"],
  "use_cases": ["author narration", "memoir", "personal essays"],
  "model_variant": "1.7B-CustomVoice",
  "notes": "Cloned from author's own recording. Full commercial rights."
}
```

### Step 3: Test Generation

Before committing to full production:

```bash
# Generate test passage
python scripts/tts_generator.py \
    --text "This is a test of the cloned voice. The quick brown fox jumps over the lazy dog. When shall we three meet again, in thunder, lightning, or in rain?" \
    --persona voice-clones/author/persona.json \
    --output test-clone.wav

# Listen critically:
# - Does it sound like the reference?
# - Are there artifacts?
# - Is emotional range preserved?
```

### Step 4: Iterate if Needed

If clone quality is poor:

| Problem | Solution |
|---------|----------|
| Doesn't sound like reference | Try longer/cleaner reference audio |
| Artifacts, glitches | Check reference for noise, try different segment |
| Monotone | Reference may lack emotional variation; record new sample |
| Wrong accent | Model may be defaulting; add accent to voice_prompt |

---

## Model-Specific Notes

### Higgs Audio V2

- Excellent zero-shot cloning from 10-15 seconds
- Preserves emotional characteristics well
- Works with `reference_audio` field in persona

### FishAudio S1

- Strong voice cloning, needs 15+ seconds
- Good multilingual preservation
- Can clone accents accurately

### General Guidance

Different models have different cloning quality. Test your reference with multiple models to find best match.

---

## Workflow Integration

### For Multi-Speaker Production

If cloning character voices for multi-speaker audiobook:

```json
{
  "speakers": {
    "narrator": {
      "persona_path": "personas/narrator-generated.json",
      "notes": "Generated voice, not cloned"
    },
    "protagonist": {
      "persona_path": "voice-clones/protagonist/persona.json",
      "notes": "Cloned from actor recording"
    },
    "mentor": {
      "persona_path": "voice-clones/mentor/persona.json",
      "notes": "Cloned from actor recording"
    }
  }
}
```

### For Author Narration

If you're cloning your own voice to narrate your own book:

1. Record 2-3 minutes of yourself reading representative passages
2. Select best 30-second segment
3. Clone and generate full audiobook
4. Review output, re-record any passages that need human touch

This hybrid approach: clone handles 90% of work, you record corrections.

---

## Quality Assurance

### Listening Checklist

- [ ] Voice timbre matches reference
- [ ] Pronunciation is correct
- [ ] No robotic artifacts
- [ ] Emotional range is natural
- [ ] Pacing feels human
- [ ] No hallucinated words or sounds
- [ ] Consistent across long passages

### A/B Testing

Generate same passage with:
1. Cloned voice
2. Generated voice (text prompt only)

Compare. Sometimes generated voices are *better* than cloned ones for certain content.

---

## Archiving

For each cloned voice, maintain:

```
voice-clones/
└── voice-name/
    ├── reference-audio/
    │   ├── original-recording.wav  # Full original
    │   └── trimmed-reference.wav   # What was used
    ├── persona.json
    ├── consent-form.pdf
    ├── test-outputs/
    │   └── test-generation-001.wav
    └── README.md                    # Notes on this voice
```

This ensures reproducibility and legal clarity.
