# ACX/Audible Technical Specifications

Non-negotiable requirements for commercial audiobook distribution.

## Audio Specifications

| Parameter | Requirement | Notes |
|-----------|-------------|-------|
| **Format** | MP3 | Required format |
| **Bit Rate** | 192 kbps CBR | Constant bit rate, not variable |
| **Sample Rate** | 44.1 kHz | Standard CD quality |
| **Channels** | Mono | Strongly recommended; must be consistent throughout |
| **Bit Depth** | 16-bit | Standard |

## Level Requirements

| Parameter | Requirement | Measurement |
|-----------|-------------|-------------|
| **RMS Level** | -23 dB to -18 dB | Average loudness |
| **Peak Level** | -3 dB maximum | Loudest moment |
| **Noise Floor** | -60 dB RMS maximum | Background noise |

### Understanding These Levels

**RMS (Root Mean Square)**: Average loudness. -23 to -18 dB means consistent, comfortable listening volume.

**Peak**: Maximum instantaneous level. -3 dB ceiling prevents clipping/distortion.

**Noise Floor**: Background hiss/hum when silent. Must be below -60 dB to be imperceptible.

## Room Tone Requirements

| Position | Duration | Purpose |
|----------|----------|---------|
| **Start of each file** | 0.5-1 second | Clean intro, prevents click |
| **End of each file** | 1-5 seconds | Clean outro, natural fade |

Room tone = silence with ambient room sound, not digital silence (which sounds unnatural).

## File Structure

### Required Files

1. **Opening Credits** (separate file)
   - Title, subtitle (if any)
   - Author name
   - Narrator name
   - "Published by [Publisher]" (if applicable)
   - Copyright year and holder

2. **Chapter Files** (one per chapter)
   - Consistent naming: `Chapter_01.mp3`, `Chapter_02.mp3`
   - Include chapter title at beginning of narration
   - Maximum length: 120 minutes per file

3. **Closing Credits** (separate file)
   - "This has been [Title]"
   - "Written by [Author]"
   - "Narrated by [Narrator]"
   - "Copyright [Year] by [Holder]"
   - "Production by [Studio]" (optional)

4. **Retail Sample** (separate file)
   - Duration: 1-5 minutes
   - Must be from the audiobook content
   - **No opening credits**
   - **No music**
   - **No explicit content**
   - Begins with narration, not credits

### File Naming Convention

```
Title_Opening_Credits.mp3
Title_Chapter_01.mp3
Title_Chapter_02.mp3
...
Title_Closing_Credits.mp3
Title_Retail_Sample.mp3
```

## Quality Requirements

### Mandatory

- No clipping or distortion
- No excessive mouth noise (clicks, pops, smacks)
- No excessive sibilance
- No long silences (>3 seconds) without purpose
- No extraneous sounds (phone, traffic, HVAC)
- Consistent volume throughout project
- Consistent tone/EQ throughout project

### Recording Environment

| Target | Professional Studio | Home Studio |
|--------|---------------------|-------------|
| Noise Criteria | NC 15-20 | NC 25-30 acceptable |
| dB(A) Empty Room | <20 dB(A) | <30 dB(A) |
| Noise Floor | -65 dB or better | -60 dB minimum |

## Post-Production Chain

Recommended processing order:

### 1. EQ (Equalization)
- High-pass filter at 80 Hz (removes rumble)
- Gentle presence boost at 2-4 kHz (clarity)
- Low-pass filter above 16 kHz (removes hiss)

### 2. Compression (ACX range; defaults in `audio_postprocess.py`)
- Ratio: 2:1 to 4:1
- Threshold: -20 to -15 dB
- Attack: 10-30 ms
- Release: 100-300 ms
- Goal: Even out dynamics, don't squash

### 3. De-Esser
- Target frequency: 4-8 kHz
- Apply to sibilance only
- Don't over-de-ess (sounds lispy)

### 4. Limiter
- Ceiling: -3 dB (ACX peak requirement)
- Don't rely on limiter to fix bad levels

### 5. Normalization
- Target RMS: -20 dB (middle of ACX range)
- Verify peaks don't exceed -3 dB after normalization

## Breath Handling

**DO keep:**
- Natural breaths between sentences
- Breaths that convey emotion

**DO remove:**
- Loud gasps
- Breaths longer than natural
- Breaths in odd places (mid-word)
- Excessive breathing during quiet passages

## Common Rejection Reasons

| Issue | Solution |
|-------|----------|
| RMS too loud | Reduce gain, re-normalize |
| RMS too quiet | Increase gain, re-normalize |
| Peaks over -3 dB | Apply limiter at -3 dB |
| Noise floor too high | Re-record or use noise reduction |
| Inconsistent volume | Compress more aggressively |
| Missing room tone | Add 0.5-1 sec silence at start/end |
| Wrong file format | Re-export as 192 kbps CBR MP3, 44.1 kHz |

## Findaway Voices Differences

| Parameter | ACX | Findaway |
|-----------|-----|----------|
| Max file length | 120 min | 77 min |
| Distribution | Audible/Amazon | 30+ platforms |
| Format | Same | Same |
| Levels | Same | Same |

## Qwen3-TTS Output Handling

### Raw Output
Qwen3-TTS outputs WAV by default. Requires post-processing for ACX compliance.

### Processing Pipeline

```
1. Generate chapter audio (Qwen3-TTS → WAV)
2. Apply EQ, compression, de-esser
3. Normalize to -20 dB RMS
4. Limit peaks to -3 dB
5. Add room tone (0.5s start, 3s end)
6. Export as MP3 (192 kbps CBR, 44.1 kHz, Mono)
7. Verify compliance (ACX Check or similar)
```

### Quality Checkpoints

- [ ] RMS between -23 and -18 dB
- [ ] Peaks below -3 dB
- [ ] Noise floor below -60 dB
- [ ] Room tone present at start/end
- [ ] No clipping or distortion
- [ ] Consistent character voices throughout
- [ ] Correct file naming
- [ ] All required files present (credits, chapters, sample)
