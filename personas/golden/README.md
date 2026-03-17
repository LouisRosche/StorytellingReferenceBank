# Golden Reference System

Regression testing infrastructure for persona voice consistency.

---

## Overview

Golden references are the canonical audio outputs for each persona. They establish what "correct" sounds like, enabling automated detection of voice drift when persona definitions or TTS models change.

**Key principle**: A persona should always sound recognizably like itself. Changes are acceptable; unintended drift is not.

---

## How It Works

### The Testing Loop

```
1. Define persona (voice_prompt, attributes)
         |
         v
2. Generate golden reference audio using standard passages
         |
         v
3. Human review: Does this sound right?
         |
    No --+-- Yes
    |         |
    v         v
Iterate    Commit as golden reference
on prompt         |
                  v
         4. Future changes trigger regression test
                  |
                  v
         5. Compare new output to golden reference
                  |
             Similarity score
                  |
         >= 0.85 --+-- < 0.85
            |            |
            v            v
          PASS        FAIL: Review change
```

### What Gets Compared

The regression system extracts MFCC (Mel-frequency cepstral coefficient) fingerprints from both the golden reference and the test audio. These fingerprints capture:

- Pitch characteristics
- Vocal texture
- Speaking pace patterns
- Prosodic features

Cosine similarity between fingerprints determines pass/fail.

---

## Test Passages

See **[test-passages.md](./test-passages.md)** for the complete passage library.

### Core Passages (Tier 1-3)

| Passage | What It Tests | Words |
|---------|---------------|-------|
| **Standard Narrative** | Pacing, tone, descriptive prose | ~250 |
| **Dialogue-Heavy** | Voice switching, emotional shifts | ~280 |
| **Emotional Peak** | Dynamic range, intensity | ~270 |
| **Technical/Expository** | Clarity, authority, articulation | ~260 |

### Genre Passages

| Passage | Best For | Words |
|---------|----------|-------|
| **Thriller/Suspense** | `narrator-thriller`, noir personas | ~240 |
| **Children's** | `narrator-childrens`, early reader | ~200 |
| **Literary/Philosophical** | Literary narrators | ~280 |
| **Memoir/Personal** | Contemporary, warm voices | ~250 |

### Minimum Coverage Requirements

- **New personas**: Standard Narrative (required)
- **Production personas**: Standard + Dialogue (recommended)
- **Premium/flagship**: All four core passages (complete)

---

## Creating Golden References

### Prerequisites

- Working TTS pipeline (`scripts/tts_generator.py`)
- Validated persona definition in `personas/examples/`
- Audio editor for quality review (Audacity, Adobe Audition)

### Step-by-Step Process

#### 1. Select test passages

Choose appropriate passages for the persona type:

```bash
# View available passages
cat personas/golden/test-passages.md
```

#### 2. Generate candidate audio

```bash
# Generate using the standard narrative passage
python scripts/tts_generator.py \
    --persona personas/examples/narrator-literary.json \
    --text-file personas/golden/passages/standard-narrative.txt \
    --output candidates/narrator-literary_standard_v1.wav
```

#### 3. Human review

Listen critically for:

- [ ] Voice matches persona definition (age, gender, accent)
- [ ] Pacing appropriate for content type
- [ ] Emotional range present but not exaggerated
- [ ] Clear articulation throughout
- [ ] No artifacts, glitches, or unnatural breaks
- [ ] Consistent quality beginning to end

**If issues exist**: Iterate on voice_prompt, regenerate, repeat.

#### 4. Process final audio

```bash
# Normalize to specifications
ffmpeg -i candidates/narrator-literary_standard_v1.wav \
    -af "loudnorm=I=-16:TP=-3:LRA=11" \
    -ar 44100 -ac 1 -acodec pcm_s16le \
    personas/golden/narrator-literary_standard.wav
```

#### 5. Update persona definition

Add golden reference path to persona JSON:

```json
{
  "quality": {
    "golden_reference": "personas/golden/narrator-literary_standard.wav",
    "last_validated": "2026-01-28",
    "validation_status": "passed"
  }
}
```

#### 6. Commit

```bash
git add personas/golden/narrator-literary_standard.wav
git add personas/examples/narrator-literary.json
git commit -m "Add golden reference for narrator-literary"
```

### Batch Generation

For generating multiple golden references:

```bash
#!/bin/bash
# generate-golden-batch.sh

PASSAGE_FILE="personas/golden/passages/standard-narrative.txt"
OUTPUT_DIR="candidates"

mkdir -p "$OUTPUT_DIR"

for persona in personas/examples/*.json; do
    id=$(jq -r .id "$persona")
    echo "Generating: $id"

    python scripts/tts_generator.py \
        --persona "$persona" \
        --text-file "$PASSAGE_FILE" \
        --output "${OUTPUT_DIR}/${id}_standard.wav"
done

echo "Review all candidates in $OUTPUT_DIR before promoting to golden/"
```

---

## Running Regression Tests

### Basic Usage

```bash
# Test all personas
python scripts/persona_regression.py

# Test specific personas
python scripts/persona_regression.py --personas narrator-literary narrator-thriller

# Custom threshold (default 0.85)
python scripts/persona_regression.py --threshold 0.90

# JSON output for CI/CD
python scripts/persona_regression.py --json
```

### Integration with CI/CD

Add to your pipeline:

```yaml
# .github/workflows/regression.yml
persona-regression:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Install dependencies
      run: pip install librosa numpy
    - name: Generate test audio
      run: python scripts/batch_produce.py --test-mode
    - name: Run regression
      run: python scripts/persona_regression.py --json > regression-report.json
    - name: Check results
      run: |
        failed=$(jq '.failed' regression-report.json)
        if [ "$failed" -gt 0 ]; then exit 1; fi
```

### Interpreting Results

```
============================================================
PERSONA REGRESSION REPORT
============================================================
✓ narrator-literary: PASS
  Similarity: 0.923 (threshold: 0.85)
✓ narrator-thriller: PASS
  Similarity: 0.891 (threshold: 0.85)
✗ narrator-childrens: FAIL: similarity 0.742 < 0.85
  Similarity: 0.742 (threshold: 0.85)
------------------------------------------------------------
Total: 3 | Passed: 2 | Failed: 1 | Skipped: 0
Success rate: 66.7%
============================================================
```

---

## Thresholds and Tuning

### Default Threshold: 0.85

This threshold balances:
- Catching meaningful voice drift
- Allowing natural variation in TTS output
- Avoiding false positives from minor model updates

### When to Adjust

| Scenario | Recommended Threshold |
|----------|----------------------|
| Production stability check | 0.85 (default) |
| Major model upgrade | 0.75 (temporary) |
| Voice cloning personas | 0.90 (stricter) |
| Development/iteration | 0.70 (lenient) |

### What Failures Mean

| Score Range | Interpretation |
|-------------|----------------|
| 0.90-1.00 | Excellent match, minimal variation |
| 0.85-0.90 | Good match, normal TTS variance |
| 0.75-0.85 | Notable drift, review recommended |
| 0.60-0.75 | Significant change, likely needs attention |
| Below 0.60 | Major deviation, investigate root cause |

### Common Failure Causes

1. **Voice prompt changes**: Intentional modifications to persona definition
2. **Model updates**: TTS engine version changes
3. **Parameter drift**: Unintended changes to inference settings
4. **Audio processing**: Different normalization or encoding

### Handling Intentional Changes

When you deliberately change a persona's voice:

```bash
# 1. Make the change
vim personas/examples/narrator-literary.json

# 2. Regenerate golden reference
python scripts/tts_generator.py \
    --persona personas/examples/narrator-literary.json \
    --text-file personas/golden/passages/standard-narrative.txt \
    --output personas/golden/narrator-literary_standard.wav

# 3. Human review new output

# 4. Update validation date
# Edit quality.last_validated in persona JSON

# 5. Commit both files together
git add personas/examples/narrator-literary.json
git add personas/golden/narrator-literary_standard.wav
git commit -m "Update narrator-literary voice (warmer tone)"
```

---

## Directory Structure

```
personas/golden/
├── README.md               # This file
├── test-passages.md        # Complete passage library
├── passages/               # Plain text passage files (for scripting)
│   ├── standard-narrative.txt
│   ├── dialogue-heavy.txt
│   ├── emotional-peak.txt
│   ├── technical-expository.txt
│   ├── thriller-genre.txt
│   ├── childrens-genre.txt
│   ├── literary-genre.txt
│   └── memoir-genre.txt
└── [persona-id]_[passage-type].wav  # Golden reference audio files
```

---

## Audio Specifications

All golden references must conform to:

| Attribute | Specification |
|-----------|---------------|
| Format | WAV (RIFF) |
| Bit depth | 16-bit PCM |
| Sample rate | 44.1 kHz |
| Channels | Mono |
| Peak level | -3 dB |
| Integrated loudness | -16 LUFS |
| Noise floor | Below -60 dB |

### Why These Specs

- **44.1 kHz / 16-bit**: Industry standard, sufficient for voice
- **Mono**: Audiobooks are mono; stereo adds no value, doubles storage
- **-16 LUFS**: Broadcast/podcast standard, comfortable listening level
- **-3 dB peak**: Headroom for playback systems

---

## Troubleshooting

### "No golden reference defined (skipped)"

The persona's JSON lacks a `quality.golden_reference` field. Add the path once you've created the golden audio.

### "Golden reference not found"

The file path in the persona JSON doesn't exist. Check the path and ensure the WAV file is committed.

### "librosa not installed"

Install the audio processing dependency:

```bash
pip install librosa
```

### "Could not extract voice fingerprints"

The audio file may be corrupted or in an unsupported format. Re-export as 16-bit WAV.

### Consistently low scores across all personas

Check for:
- Different TTS model version
- Changed inference parameters (temperature, etc.)
- Audio processing differences (normalization, encoding)

---

## Persona Status

| Persona | Golden Ref | Tier | Last Validated |
|---------|------------|------|----------------|
| character-child | pending | - | - |
| character-gruff-mentor | pending | - | - |
| character-teen | pending | - | - |
| narrator-australian | pending | - | - |
| narrator-british | pending | - | - |
| narrator-caribbean | pending | - | - |
| narrator-childrens | pending | - | - |
| narrator-comedy | pending | - | - |
| narrator-elder-authority | pending | - | - |
| narrator-french | pending | - | - |
| narrator-global-literary | pending | - | - |
| narrator-horror | pending | - | - |
| narrator-indian-english | pending | - | - |
| narrator-latinx-bilingual | pending | - | - |
| narrator-literary | pending | - | - |
| narrator-literary-female | pending | - | - |
| narrator-nonbinary-contemporary | pending | - | - |
| narrator-thriller | pending | - | - |
| narrator-warm-female | pending | - | - |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-28 | Infrastructure complete: passages, documentation, workflow |
| 2026-01-27 | Initial README with basic structure |
