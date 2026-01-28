# AI Sound Design Research for Audiobook Production

Research conducted: 2026-01-28

This document evaluates AI-powered tools for generating music and sound effects to enhance audiobook production with immersive audio experiences.

---

## Executive Summary

The AI audio generation landscape has matured significantly, with viable options for both music and sound effects generation. For production use, we recommend:

- **Music Generation**: Suno API (via third-party providers) for commercial tracks, MusicGen for open-source/local generation
- **Sound Effects**: ElevenLabs Text-to-SFX API for custom effects, Freesound API for traditional library access
- **Mixing**: FFmpeg sidechaincompress for automated ducking, pydub for basic audio manipulation

---

## AI Music Generation

### 1. Suno AI

**Overview**: Leading commercial AI music generator with full song creation capabilities including vocals.

**Capabilities**:
- Full song generation from text prompts (music + vocals + lyrics)
- Instrumental-only generation
- Multiple style/genre support
- Fine-grained control over tempo, key, rhythm, dynamics
- Watermark-free commercial output
- Song variations and extensions

**API Access**:
- No official public API from Suno directly
- Third-party providers offer production-ready REST APIs

**Pricing** (via third-party providers):

| Provider | Price/Generation | Notes |
|----------|-----------------|-------|
| Official (indirect) | ~$0.04 | Per creation call |
| [SunoAPI.com](https://sunoapi.org/) | ~$0.01 | 75% savings vs official |
| [Lyrica API](https://sunoapi.info/) | $0.041-0.05 | Volume discounts |
| [APIframe](https://apiframe.ai/suno-api-for-ai-music-generation) | Variable | Production-ready |

**Model Versions**: V5, V4.5 Plus, V4.5 All, V4.5, V4

**Pros**:
- Highest quality AI-generated music
- Full vocal support
- Commercially cleared
- Active development

**Cons**:
- No direct official API
- Reliance on third-party providers
- Higher cost than open-source alternatives
- Potential legal gray areas (settled with Warner 2025)

**Best For**: Background music beds, chapter intros/outros, mood-setting ambient tracks

---

### 2. Udio AI

**Overview**: Competitor to Suno with focus on pop/EDM production.

**Capabilities**:
- Text-to-music generation
- Strong pop and EDM output
- Songs up to 2:10 minutes (v1.5)
- Audio-to-audio transformation

**Consumer Plans**:

| Plan | Price | Songs/Month |
|------|-------|-------------|
| Free | $0 | 10/day |
| Standard | $10/mo | 1,200 |
| Pro | $30/mo | Unlimited |

**API Access**: No direct public API; available through third-party providers like [MusicAPI.ai](https://musicapi.ai/udio-api) and [UdioAPI.pro](https://udioapi.pro/)

**Model Versions**: v1.0, v1.5, v1.5 Allegro (studio quality)

**Legal Status**: Settled with UMG (2025), now partnering with major labels

**Best For**: Energetic scenes, modern genre audiobooks, younger audience content

---

### 3. Meta MusicGen (Open Source)

**Overview**: Open-source music generation from Meta's AudioCraft suite.

**Capabilities**:
- Text-to-music generation
- Melody conditioning (generate music matching a melody)
- Multiple model sizes: 300M, 1.5B, 3.3B parameters
- Local/self-hosted deployment
- Part of [AudioCraft](https://ai.meta.com/resources/models-and-libraries/audiocraft/) library

**Availability**:
- [Hugging Face](https://huggingface.co/facebook/musicgen-large): `facebook/musicgen-large`
- PyTorch library via `pip install audiocraft`
- Requires Python 3.9+, PyTorch 2.0+

**Pricing**: Free (open source)

**Licensing**: **Non-commercial use only** for pretrained models

**Technical Requirements**:
- GPU recommended (CUDA)
- 8GB+ VRAM for large model
- ~30 seconds generation time on consumer GPU

**Pros**:
- Free and open source
- Local deployment (privacy)
- No API dependencies
- Good for experimentation

**Cons**:
- Non-commercial license restricts production use
- Lower quality than Suno/Udio
- Requires GPU infrastructure
- No vocals

**Best For**: Prototyping, non-commercial projects, instrumental beds

---

### 4. Stability AI - Stable Audio

**Overview**: Enterprise-grade audio model from Stability AI.

**Capabilities**:
- Text-to-audio generation
- Audio-to-audio transformation
- Audio inpainting
- Sound effects and music
- Strong prompt adherence

**Pricing**:
- [Community License](https://stability.ai/license): Free for revenue <$1M/year
- Enterprise: Custom pricing
- API: Usage-based via [platform.stability.ai](https://platform.stability.ai/pricing)

**Open Source Option**: [Stable Audio Open](https://huggingface.co/stabilityai/stable-audio-open-1.0) available on Hugging Face (trained on CC-licensed audio)

**Best For**: Enterprise deployments, combined music/SFX generation

---

### 5. Other Music Options

| Tool | Type | Best For | Pricing |
|------|------|----------|---------|
| [Soundraw](https://soundraw.io/) | Commercial | Quick royalty-free tracks | Subscription |
| [AIVA](https://www.aiva.ai/) | Commercial | Classical/orchestral | Freemium |
| [Beatoven.ai](https://www.beatoven.ai/) | Commercial | Adaptive podcast/film scoring | Subscription |
| [Mubert](https://mubert.com/) | Commercial | Streaming-safe background | API available |
| [Loudly](https://www.loudly.com/) | Commercial | Ad/commercial music | Subscription |
| [ACE-Step](https://github.com/ace-step/ace-step) | Open Source | 4-min songs in 20 seconds | Free |

---

## AI Sound Effects Generation

### 1. ElevenLabs Sound Effects API

**Overview**: Industry-leading text-to-sound-effects API.

**Capabilities**:
- Text description to audio effect
- Precise duration control (up to 22-30 seconds)
- Looping sound generation for ambiance
- Prompt influence adjustment
- Multiple output formats (MP3, WAV, PCM)

**API Endpoint**: `POST /v1/sound-generation`

**Model**: `eleven_text_to_sound_v2`

**Pricing**:

| Generation Type | Cost |
|-----------------|------|
| Auto-duration | 200 credits |
| Manual duration | 40 credits/second |

Credit costs vary by plan tier. See [ElevenLabs pricing](https://elevenlabs.io/pricing).

**Code Example**:
```python
from elevenlabs import ElevenLabs

client = ElevenLabs(api_key="...")
audio = client.text_to_sound_effects.convert(
    text="Heavy wooden door creaking open slowly in an old castle",
    duration_seconds=3.0,
    prompt_influence=0.5
)
```

**Output Quality**:
- MP3 192kbps requires Creator tier+
- PCM 44.1kHz requires Pro tier+

**Pros**:
- High quality output
- Precise control
- Commercial license included
- Same API as TTS (unified billing)

**Cons**:
- Credit-based pricing adds up
- 22-30 second max duration
- Requires internet connection

**Best For**: Custom spot effects, unique sounds, tight integration with ElevenLabs TTS

---

### 2. Stability AI - Stable Audio for SFX

**Capabilities**: Combined music and SFX generation in one model.

**Pros**: Enterprise-grade, combined workflow
**Cons**: Less specialized for SFX than ElevenLabs

---

### 3. Adobe Firefly Audio

**Overview**: Web-based AI sound generator integrated with Adobe Creative Cloud.

**Capabilities**:
- Text-to-sound effects
- Reference audio input
- Voice/action recording as input

**Access**: Adobe Creative Cloud subscription

**Best For**: Users already in Adobe ecosystem

---

### 4. Free/Open Alternatives

| Tool | Description | API |
|------|-------------|-----|
| [SFX Engine](https://sfxengine.com/) | Free AI sound effects | Web only |
| [OptimizerAI](https://www.optimizerai.xyz/) | Unlimited sound generation | Web + API |
| Meta AudioGen | Open-source SFX generation | Local |

---

## Traditional Sound Libraries with APIs

### 1. Freesound

**Overview**: Largest Creative Commons sound library (400,000+ sounds).

**API**: Full REST API with Python client

**Capabilities**:
- Text search with filters
- Content-based similarity search
- Download previews (MP3/OGG) or full quality (OAuth2)
- Upload/comment/bookmark

**Pricing**: Free (API key required)

**Licensing**: Varies by upload (CC0, CC-BY, CC-Sampling+)

**Python Client**:
```python
import freesound

client = freesound.FreesoundClient()
client.set_token("<api_key>", "token")

# Search for door sounds, high-rated, CC0 license
results = client.text_search(
    query='door creak',
    filter='duration:[0.0 TO 15.0] avg_rating:[4.0 TO 5.0] license:"Creative Commons 0"',
    fields="id,name,previews,license"
)

for sound in results:
    sound.retrieve_preview("./sfx/", sound.name + ".mp3")
```

**Documentation**: [freesound.org/docs/api/](https://freesound.org/docs/api/)

**Best For**: Large variety, budget-conscious production, CC-licensed needs

---

### 2. BBC Sound Effects Archive

**Overview**: 33,000+ archival sounds from BBC's 100+ year history.

**Licensing**: **Personal, educational, research only** - NOT for commercial

**Best For**: Non-commercial projects, prototyping

---

### 3. Commercial Libraries

| Library | Sounds | API | Commercial |
|---------|--------|-----|------------|
| [Zapsplat](https://www.zapsplat.com/) | 160,000+ | No | Yes (attribution) |
| [Soundsnap](https://www.soundsnap.com/) | Large | Yes | Yes (subscription) |
| [Pixabay Audio](https://pixabay.com/sound-effects/) | Medium | Yes | Yes (royalty-free) |

---

## Audio Mixing and Ducking

### Volume Ducking (Sidechain Compression)

Automatically reduce background audio when narration plays.

**FFmpeg Implementation**:
```bash
ffmpeg -i narration.wav -i background_music.mp3 \
  -filter_complex "[1:a]sidechaincompress=threshold=0.03:ratio=4:attack=200:release=1000[bg];[0:a][bg]amix=duration=first" \
  -c:a aac output.m4a
```

**Key Parameters**:
- `threshold`: Level at which ducking triggers (0.02-0.05 typical)
- `ratio`: How much to reduce (3:1 to 6:1 for music beds)
- `attack`: How fast to duck (100-300ms)
- `release`: How fast to recover (500-2000ms)

**Pydub Alternative** (manual envelope):
```python
from pydub import AudioSegment

narration = AudioSegment.from_file("narration.wav")
music = AudioSegment.from_file("music.mp3")

# Reduce music volume
music_ducked = music - 12  # -12dB during speech

# Overlay with cross-fade
combined = music_ducked.overlay(narration, position=0)
```

Note: Pydub lacks automatic sidechain compression. Use FFmpeg or implement voice activity detection for true dynamic ducking.

---

## ACX/Audible Considerations

### Music and Sound Effects Rules

From [ACX Help](https://help.acx.com/s/article/can-i-add-music-to-my-audiobook):

> "Some audiobooks use sound effects or music, but the simplest and cheapest cue is just a pause."

**Key Requirements**:
1. **Retail Sample**: Must start with narration, NOT music or credits
2. **No AI Narration**: ACX does not accept AI-narrated audiobooks (TTS) - sound design is separate
3. **Quality**: All audio must meet ACX specs (-23 to -18 dB RMS, -3 dB peak, -60 dB noise floor)
4. **Consistency**: Music/SFX must not violate RMS/peak requirements

**Recommendation**: Use sound design sparingly and ensure it enhances rather than distracts. Test final mix against ACX specs.

---

## Best Practices for Immersive Audiobooks

### Production Guidelines

1. **Balance and Restraint**: Background sounds should enhance, not distract
2. **2-Minute Loop Rule**: Listeners notice looped audio after ~2 minutes
3. **Subtle Panning**: Keep panning within 20 degrees to avoid listener fatigue
4. **Scene-Appropriate**: Match ambiance to setting (beach = waves, forest = birds)
5. **Multi-Device Testing**: Check on headphones, car speakers, phone speakers

### Sound Design Categories

| Category | Example | Tool Recommendation |
|----------|---------|---------------------|
| Ambiance | Room tone, outdoor atmosphere | Freesound, ElevenLabs |
| Spot Effects | Door slam, footsteps | ElevenLabs, Freesound |
| Music Beds | Tension underscore, chapter intros | Suno, MusicGen |
| Transitions | Whooshes, risers | ElevenLabs, pre-made libraries |
| Stingers | Short musical punctuation | Suno, pre-made libraries |

---

## Recommended Tool Stack

### Tier 1: Full Commercial Production

| Component | Tool | Cost |
|-----------|------|------|
| Music Generation | Suno API (via provider) | ~$0.01-0.04/track |
| Sound Effects | ElevenLabs SFX API | ~200 credits/effect |
| Library SFX | Freesound (CC0) | Free |
| Mixing | FFmpeg + pydub | Free |

### Tier 2: Budget Production

| Component | Tool | Cost |
|-----------|------|------|
| Music Generation | MusicGen (if non-commercial) | Free |
| Sound Effects | Freesound API | Free |
| Library SFX | Zapsplat | Free (with attribution) |
| Mixing | FFmpeg + pydub | Free |

### Tier 3: Enterprise

| Component | Tool | Cost |
|-----------|------|------|
| Music + SFX | Stability AI Stable Audio | Enterprise pricing |
| Additional SFX | ElevenLabs Scale/Business | Volume discounts |
| Library | Soundsnap subscription | ~$249/year |
| Mixing | Professional DAW | Variable |

---

## Integration Approach

The recommended architecture follows the existing provider abstraction pattern used for TTS:

1. **Provider Interface**: Abstract base class for music/SFX generation
2. **Multiple Backends**: Suno, ElevenLabs, Freesound, MusicGen
3. **Cue Parser**: Extract sound cues from manuscript markup
4. **Mixer**: Combine TTS output with generated audio using FFmpeg
5. **Validator**: Ensure final output meets ACX specs

See `docs/sound-design-architecture.md` for detailed implementation design.

---

## Sources

### AI Music
- [Suno Pricing](https://suno.com/pricing)
- [SunoAPI Documentation](https://docs.sunoapi.org/)
- [Udio Pricing](https://www.udio.com/pricing)
- [Meta AudioCraft](https://ai.meta.com/resources/models-and-libraries/audiocraft/)
- [MusicGen on Hugging Face](https://huggingface.co/facebook/musicgen-large)
- [Stability AI Stable Audio](https://stability.ai/stable-audio)

### AI Sound Effects
- [ElevenLabs Sound Effects](https://elevenlabs.io/sound-effects)
- [ElevenLabs SFX API Documentation](https://elevenlabs.io/docs/api-reference/text-to-sound-effects/convert)
- [Adobe Firefly Audio](https://www.adobe.com/products/firefly/features/sound-effect-generator.html)

### Sound Libraries
- [Freesound API Documentation](https://freesound.org/docs/api/)
- [Freesound Python Client](https://github.com/MTG/freesound-python)
- [Zapsplat](https://www.zapsplat.com/)

### Mixing and Production
- [FFmpeg Sidechain Compression](https://ffmpeg.org/pipermail/ffmpeg-user/2018-August/040933.html)
- [Pydub Documentation](https://github.com/jiaaro/pydub)
- [ACX Audio Submission Requirements](https://help.acx.com/s/article/what-are-the-acx-audio-submission-requirements)
- [ACX Music and Sound Effects](https://help.acx.com/s/article/can-i-add-music-to-my-audiobook)

### Best Practices
- [Audio Drama Sound Design](https://www.11thhouraudio.com/learn/sound-design/audio-drama-sound-design/)
- [Immersive Audiobook Production](https://saspod.com/blog/post/how-to-produce-an-immersive-audiobook-with-music-and-sound-design)
- [Audiobook Producers Guide](https://www.bensound.com/blog/creation-editing/music-audiobook-producers/)
