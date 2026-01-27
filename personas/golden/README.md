# Golden Reference Audio

This directory contains golden reference audio files for persona regression testing.

## Purpose

Golden references establish the "correct" voice for each persona. When persona definitions change (voice_prompt updates, model variant changes), regression tests compare new output against these references to detect drift.

## File Naming

```
{persona-id}.wav
```

Example: `narrator-literary-female.wav`

## Creating Golden References

1. Generate audio using the persona with a standard test passage
2. Manually verify quality meets production standards
3. Save as 16-bit WAV, 44.1kHz mono
4. Update persona's `quality.golden_reference` field

## Standard Test Passage

Use this passage for all golden references (covers emotional range):

> "The morning light filtered through the curtains, casting long shadows across the empty room. She hadn't expected this—the quiet, the stillness, the weight of absence. But here it was. And somewhere, perhaps, hope remained."

## Regression Testing

```bash
python scripts/persona_regression.py --golden-dir personas/golden --test-dir test_output
```

Threshold: 0.85 cosine similarity on MFCC fingerprints.

## Files

| Persona | Status | Last Updated |
|---------|--------|--------------|
| narrator-literary-female | pending | — |
| narrator-warm-female | pending | — |
| narrator-thriller | pending | — |
| narrator-british | pending | — |
| narrator-french | pending | — |
| character-teen | pending | — |
