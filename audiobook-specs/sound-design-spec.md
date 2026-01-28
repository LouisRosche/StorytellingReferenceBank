# Sound Design Specification for Audiobooks

Technical specification for integrating music and sound effects into audiobook production.

---

## Manuscript Markup Format

### Overview

Sound cues are embedded in manuscripts using a bracket notation that the pipeline parser extracts before TTS generation. Cues are processed into a timeline synchronized with the narration.

### Cue Syntax

```
[TYPE: identifier COMMAND]
```

**Components**:
- `TYPE`: `SFX`, `MUSIC`, `AMBIANCE`, or `SILENCE`
- `identifier`: Snake_case name for the sound asset
- `COMMAND`: Action to perform (START, STOP, FADE_IN, FADE_OUT, DUCK, etc.)

---

## Sound Effect Cues (SFX)

### Basic Spot Effects

Play once at the marked position.

```
[SFX: door_creak]
[SFX: footsteps_wood]
[SFX: thunder_rumble]
[SFX: glass_break]
```

### Effects with Duration

```
[SFX: rain_heavy 5s]
[SFX: clock_ticking 10s]
```

### Effects with Volume

```
[SFX: whisper_wind -6dB]
[SFX: explosion +3dB]
```

### Combined Parameters

```
[SFX: heartbeat 8s -3dB]
```

### Effect Sequences

Multiple effects triggered in order:

```
[SFX: door_open, footsteps_enter, door_close]
```

---

## Music Cues (MUSIC)

### Start Music

```
[MUSIC: tense_underscore START]
[MUSIC: romantic_theme START]
[MUSIC: action_chase START]
```

### Stop Music

```
[MUSIC: STOP]
[MUSIC: tense_underscore STOP]
```

### Fade In/Out

```
[MUSIC: peaceful_morning FADE_IN 3s]
[MUSIC: battle_theme FADE_OUT 5s]
```

### Cross-Fade Between Tracks

```
[MUSIC: sad_theme CROSSFADE happy_theme 4s]
```

### Volume Control

```
[MUSIC: background_score -12dB]
[MUSIC: DUCK -15dB]      <!-- Lower music during speech -->
[MUSIC: UNDUCK]          <!-- Restore music volume -->
```

### Music Bed (Continuous Underscore)

```
[MUSIC: chapter_intro START -15dB LOOP]
...chapter content...
[MUSIC: FADE_OUT 5s]
```

---

## Ambiance Cues (AMBIANCE)

Continuous environmental sound that loops.

### Start Ambiance

```
[AMBIANCE: forest_birds START]
[AMBIANCE: city_traffic START -9dB]
[AMBIANCE: ocean_waves START LOOP]
```

### Layer Multiple Ambiances

```
[AMBIANCE: rain_light START]
[AMBIANCE: fireplace_crackle START]
```

### Stop Ambiance

```
[AMBIANCE: STOP_ALL]
[AMBIANCE: forest_birds STOP]
[AMBIANCE: forest_birds FADE_OUT 3s]
```

### Ambiance Transitions

```
[AMBIANCE: indoor_office CROSSFADE outdoor_park 2s]
```

---

## Silence Cues (SILENCE)

Insert deliberate silence or room tone.

```
[SILENCE: 2s]           <!-- 2 seconds of room tone -->
[SILENCE: beat]         <!-- Short dramatic pause (0.5s) -->
[SILENCE: long_pause]   <!-- Extended pause (3s) -->
```

---

## Generation Hints

Provide generation parameters for AI-generated sounds.

### AI Music Generation

```
[MUSIC: chapter_theme START]
<!-- @generate: genre=orchestral, mood=mysterious, tempo=slow, duration=60s -->
```

```
[MUSIC: action_sequence START]
<!-- @generate: genre=electronic, mood=intense, tempo=140bpm, duration=90s -->
```

### AI Sound Effect Generation

```
[SFX: alien_communication]
<!-- @generate: "strange warbling electronic alien voice communication sound" -->
```

```
[SFX: magic_spell_cast]
<!-- @generate: "mystical sparkle whoosh with rising pitch and ethereal chime" -->
```

---

## Library References

Reference sounds from external libraries.

### Freesound Integration

```
[SFX: door_creak]
<!-- @freesound: id=12345 -->
```

```
[AMBIANCE: forest_night]
<!-- @freesound: query="forest night owl", license=cc0, min_rating=4.0 -->
```

### Local Asset Path

```
[SFX: custom_logo_sound]
<!-- @file: assets/sfx/brand_logo_sting.wav -->
```

---

## Cue Placement Examples

### Scene Opening

```markdown
[AMBIANCE: medieval_tavern START -12dB]
[SFX: door_creak]

The heavy oak door groaned as Elena pushed it open. The tavern fell silent.

[SFX: footsteps_stone 3s]
[MUSIC: tension_theme FADE_IN 4s -18dB]
```

### Action Sequence

```markdown
[MUSIC: chase_theme START]
[AMBIANCE: city_alley START]

Marcus sprinted through the narrow streets, his footsteps echoing off wet cobblestones.

[SFX: running_footsteps]

Behind him, the guards shouted commands.

[SFX: guards_shouting]
[SFX: sword_unsheath]

He ducked into a doorway, heart pounding.

[SFX: heavy_breathing]
[MUSIC: DUCK -20dB]
[SILENCE: beat]
[MUSIC: UNDUCK]
```

### Scene Transition

```markdown
[AMBIANCE: FADE_OUT 2s]
[MUSIC: FADE_OUT 3s]
[SILENCE: 2s]

* * *

[AMBIANCE: morning_birds FADE_IN 2s]
[MUSIC: peaceful_dawn FADE_IN 3s -15dB]

The next morning arrived with unexpected warmth.
```

### Chapter End

```markdown
And with that, she finally understood.

[MUSIC: revelation_theme FADE_IN 3s]
[SILENCE: 2s]
[MUSIC: FADE_OUT 5s]

<!-- END CHAPTER -->
```

---

## Audio Mixing Specifications

### Volume Hierarchy

Default volume levels (relative to narration at 0 dB):

| Layer | Default Level | Range |
|-------|--------------|-------|
| Narration | 0 dB | Fixed reference |
| Sound Effects | -6 dB | -12 to +3 dB |
| Music (active) | -15 dB | -20 to -12 dB |
| Music (ducked) | -24 dB | -30 to -18 dB |
| Ambiance | -18 dB | -24 to -12 dB |

### Ducking Parameters

When narration plays over music/ambiance:

| Parameter | Value | Description |
|-----------|-------|-------------|
| Duck Level | -24 dB | Music level during speech |
| Attack Time | 200 ms | How fast to duck |
| Hold Time | 100 ms | Minimum duck duration |
| Release Time | 800 ms | How fast to restore |
| Threshold | -40 dB | Speech detection level |

### Fade Parameters

Default fade durations:

| Fade Type | Default | Range |
|-----------|---------|-------|
| Quick fade | 0.5s | 0.1-1.0s |
| Normal fade | 2.0s | 1.0-4.0s |
| Slow fade | 5.0s | 3.0-10.0s |
| Cross-fade | 3.0s | 1.0-6.0s |

### Timing Offsets

Cues can be offset from their text position:

```
[SFX: thunder_rumble OFFSET -0.5s]   <!-- Play 0.5s before text -->
[SFX: reaction_gasp OFFSET +0.2s]    <!-- Play 0.2s after text -->
```

---

## File Format Requirements

### Source Audio Assets

| Parameter | Requirement |
|-----------|-------------|
| Format | WAV, FLAC, or MP3 (320kbps) |
| Sample Rate | 44.1 kHz or 48 kHz |
| Bit Depth | 16-bit minimum, 24-bit preferred |
| Channels | Stereo or Mono |

### Generated Audio

AI-generated music and SFX should meet:

| Parameter | Requirement |
|-----------|-------------|
| Format | WAV (working), MP3 for delivery |
| Sample Rate | 44.1 kHz |
| Duration (SFX) | 0.1s - 30s |
| Duration (Music) | 30s - 300s |

### Final Output (ACX Compliance)

The mixed output must meet ACX specifications:

| Parameter | Requirement |
|-----------|-------------|
| Format | MP3, 192 kbps CBR |
| Sample Rate | 44.1 kHz |
| Channels | Mono |
| RMS Level | -23 to -18 dB |
| Peak Level | -3 dB maximum |
| Noise Floor | -60 dB maximum |

---

## Asset Naming Convention

### Sound Effects

```
sfx_{category}_{description}_{variant}.wav

Examples:
sfx_door_creak_wooden.wav
sfx_footsteps_stone_slow.wav
sfx_impact_punch_heavy.wav
sfx_nature_thunder_distant.wav
```

### Music Tracks

```
music_{mood}_{genre}_{tempo}_{variant}.wav

Examples:
music_tense_orchestral_slow_01.wav
music_happy_acoustic_medium_loop.wav
music_action_electronic_fast_chase.wav
```

### Ambiance

```
amb_{environment}_{detail}_{variant}.wav

Examples:
amb_forest_daytime_birds.wav
amb_city_traffic_heavy.wav
amb_interior_office_quiet.wav
```

---

## Cue File Format (JSON)

Parsed cues are stored as JSON for pipeline processing:

```json
{
  "version": "1.0",
  "source_file": "chapter_01.txt",
  "cues": [
    {
      "type": "AMBIANCE",
      "id": "forest_birds",
      "command": "START",
      "position_chars": 0,
      "position_time_est": 0.0,
      "params": {
        "volume_db": -12,
        "loop": true
      },
      "generation_hint": null,
      "asset_path": null
    },
    {
      "type": "SFX",
      "id": "door_creak",
      "command": "PLAY",
      "position_chars": 45,
      "position_time_est": 2.5,
      "params": {
        "duration_sec": null,
        "volume_db": -6,
        "offset_sec": 0
      },
      "generation_hint": "heavy wooden door creaking open slowly",
      "asset_path": "sfx/door_creak_wooden.wav"
    },
    {
      "type": "MUSIC",
      "id": "tense_underscore",
      "command": "FADE_IN",
      "position_chars": 200,
      "position_time_est": 12.0,
      "params": {
        "fade_duration_sec": 3.0,
        "volume_db": -18,
        "loop": true
      },
      "generation_hint": {
        "genre": "orchestral",
        "mood": "mysterious",
        "tempo": "slow"
      },
      "asset_path": null
    }
  ],
  "metadata": {
    "parsed_at": "2026-01-28T10:30:00Z",
    "total_cues": 3,
    "cue_types": {
      "SFX": 1,
      "MUSIC": 1,
      "AMBIANCE": 1
    }
  }
}
```

---

## Pipeline Integration

### Processing Order

1. **Parse** - Extract cues from manuscript, remove from TTS text
2. **Resolve** - Match cues to assets (library lookup or generation queue)
3. **Generate** - Create AI music/SFX for unresolved cues
4. **TTS** - Generate narration audio
5. **Align** - Calculate cue timestamps from text positions
6. **Mix** - Combine narration with sound layers
7. **Master** - Apply ACX post-processing
8. **Validate** - Check final output meets specs

### Cue Extraction Regex

```python
import re

CUE_PATTERN = re.compile(
    r'\[(?P<type>SFX|MUSIC|AMBIANCE|SILENCE):\s*'
    r'(?P<content>[^\]]+)\]'
    r'(?:\s*<!--\s*@(?P<directive>\w+):\s*(?P<params>[^>]+)\s*-->)?',
    re.MULTILINE | re.IGNORECASE
)

def extract_cues(text: str) -> list:
    cues = []
    for match in CUE_PATTERN.finditer(text):
        cues.append({
            'type': match.group('type').upper(),
            'content': match.group('content').strip(),
            'directive': match.group('directive'),
            'params': match.group('params'),
            'position': match.start(),
        })
    return cues

def strip_cues(text: str) -> str:
    """Remove cues from text for TTS processing."""
    return CUE_PATTERN.sub('', text)
```

---

## Validation Rules

### Cue Validation

1. Every `START` must have a corresponding `STOP` or `FADE_OUT`
2. No overlapping music tracks (use crossfade for transitions)
3. Asset IDs must be valid identifiers (alphanumeric + underscore)
4. Volume must be in range -60 to +12 dB
5. Duration must be positive and reasonable (0.1s - 600s)

### Mix Validation

1. Combined audio must not exceed -3 dB peak
2. RMS must stay within -23 to -18 dB range
3. No clipping or distortion
4. Room tone requirements still apply at start/end

### Asset Validation

1. All referenced assets must exist or have generation hints
2. Audio files must meet format requirements
3. Looped audio must have clean loop points

---

## Error Handling

### Missing Assets

```json
{
  "error": "ASSET_NOT_FOUND",
  "cue_id": "mysterious_sound",
  "resolution": "GENERATE",
  "fallback": "SILENCE"
}
```

### Generation Failure

```json
{
  "error": "GENERATION_FAILED",
  "cue_id": "alien_communication",
  "provider": "elevenlabs",
  "resolution": "RETRY",
  "max_retries": 3,
  "fallback": "SKIP"
}
```

### Mix Failure

```json
{
  "error": "MIX_CLIPPING",
  "position_sec": 45.2,
  "peak_db": -1.5,
  "resolution": "AUTO_ATTENUATE",
  "adjustment_db": -3
}
```

---

## Configuration

### Default Configuration File

`sound_design_config.json`:

```json
{
  "providers": {
    "music": {
      "primary": "suno",
      "fallback": "musicgen"
    },
    "sfx": {
      "primary": "elevenlabs",
      "fallback": "freesound"
    }
  },
  "mixing": {
    "duck_level_db": -24,
    "duck_attack_ms": 200,
    "duck_release_ms": 800,
    "default_sfx_volume_db": -6,
    "default_music_volume_db": -15,
    "default_ambiance_volume_db": -18
  },
  "generation": {
    "music_default_duration_sec": 120,
    "sfx_default_duration_sec": 3,
    "retry_count": 3
  },
  "output": {
    "format": "mp3",
    "bitrate": 192,
    "sample_rate": 44100,
    "channels": 1
  },
  "assets": {
    "cache_dir": ".sound_cache/",
    "library_paths": [
      "assets/sfx/",
      "assets/music/",
      "assets/ambiance/"
    ]
  }
}
```
