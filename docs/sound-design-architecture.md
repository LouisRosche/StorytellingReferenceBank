# Sound Design Pipeline Architecture

Technical architecture for integrating AI-powered sound design into the audiobook production pipeline.

**Related**: `audiobook-specs/sound-design-spec.md` (cue format) · `docs/sound-design-research.md` (tool evaluation) · `audiobook-specs/acx-requirements.md` (compliance)

---

## Overview

The sound design system extends the existing `batch_produce.py` pipeline with modular components for:

1. **Cue Extraction** - Parse sound cues from manuscripts
2. **Asset Resolution** - Match cues to existing assets or queue for generation
3. **Audio Generation** - Generate music/SFX via AI providers
4. **Audio Mixing** - Combine narration with sound layers
5. **Mastering** - Ensure ACX compliance

The architecture follows the existing patterns: provider abstraction, configuration-driven, and pipeline stages.

---

## System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MANUSCRIPT INPUT                                    │
│                     (with embedded sound cues)                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CUE PARSER                                         │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐          │
│  │ Extract Cues    │───▶│ Clean Text      │───▶│ Generate        │          │
│  │ [SFX:...] etc   │    │ (for TTS)       │    │ Cue Timeline    │          │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘
                    │                                       │
                    ▼                                       ▼
┌───────────────────────────────┐         ┌───────────────────────────────────┐
│        TTS PIPELINE           │         │       ASSET RESOLVER               │
│  (existing batch_produce)     │         │  ┌─────────────────────────────┐  │
│                               │         │  │ Library Lookup              │  │
│  manuscript_to_chapters       │         │  │ (local files, Freesound)    │  │
│           │                   │         │  └─────────────────────────────┘  │
│           ▼                   │         │              │                    │
│  tts_generator                │         │              ▼                    │
│           │                   │         │  ┌─────────────────────────────┐  │
│           ▼                   │         │  │ Generation Queue            │  │
│  raw chapter audio            │         │  │ (missing assets)            │  │
│                               │         │  └─────────────────────────────┘  │
└───────────────────────────────┘         └───────────────────────────────────┘
                    │                                       │
                    │                                       ▼
                    │               ┌──────────────────────────────────────────┐
                    │               │          AUDIO GENERATORS                 │
                    │               │  ┌────────────┬────────────┬──────────┐  │
                    │               │  │ Music      │ SFX        │ Ambiance │  │
                    │               │  │ Provider   │ Provider   │ Provider │  │
                    │               │  └────────────┴────────────┴──────────┘  │
                    │               │        │            │            │       │
                    │               │        ▼            ▼            ▼       │
                    │               │  ┌─────────────────────────────────────┐ │
                    │               │  │        Generated Assets              │ │
                    │               │  └─────────────────────────────────────┘ │
                    │               └──────────────────────────────────────────┘
                    │                                       │
                    ▼                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            AUDIO MIXER                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         Timeline Composer                            │    │
│  │  ┌──────────────────────────────────────────────────────────────┐   │    │
│  │  │ [AMBIANCE]═══════════════════════════════════════════════════│   │    │
│  │  │ [MUSIC]──────────────▶ DUCK ────────▶ FADE_OUT               │   │    │
│  │  │ [NARRATION]===========================================       │   │    │
│  │  │ [SFX]     ▲        ▲              ▲        ▲                 │   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      Ducking Engine (FFmpeg)                         │    │
│  │                    Sidechain compression when                        │    │
│  │                    narration is present                              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MASTERING PIPELINE                                    │
│                    (existing audio_postprocess.py)                           │
│                                                                              │
│  EQ ──▶ Compression ──▶ Limiter ──▶ Normalize ──▶ Room Tone                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ACX VALIDATOR                                       │
│                    (existing acx_validator.py)                               │
│                                                                              │
│  RMS check ──▶ Peak check ──▶ Noise floor ──▶ Format check                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FINAL OUTPUT                                       │
│                    ACX-compliant MP3 with                                    │
│                    integrated sound design                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. Cue Parser (`cue_parser.py`)

Extracts sound cues from manuscripts and prepares text for TTS.

```python
"""
Sound cue parser for manuscripts.

Extracts [SFX:...], [MUSIC:...], [AMBIANCE:...], [SILENCE:...] cues
and their associated generation hints.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
import re


class CueType(Enum):
    SFX = "sfx"
    MUSIC = "music"
    AMBIANCE = "ambiance"
    SILENCE = "silence"


class CueCommand(Enum):
    PLAY = "play"           # One-shot
    START = "start"         # Begin continuous
    STOP = "stop"           # End continuous
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    CROSSFADE = "crossfade"
    DUCK = "duck"
    UNDUCK = "unduck"


@dataclass
class SoundCue:
    """Parsed sound cue from manuscript."""
    type: CueType
    id: str
    command: CueCommand
    position_chars: int

    # Optional parameters
    duration_sec: Optional[float] = None
    volume_db: float = 0.0
    fade_duration_sec: float = 2.0
    offset_sec: float = 0.0
    loop: bool = False
    crossfade_target: Optional[str] = None

    # Generation hint for AI providers
    generation_hint: Optional[Dict[str, Any]] = None

    # Resolved asset path (filled by resolver)
    asset_path: Optional[str] = None

    # Calculated timing (filled by mixer)
    start_time_sec: Optional[float] = None
    end_time_sec: Optional[float] = None


@dataclass
class ParseResult:
    """Result of parsing a manuscript for cues."""
    clean_text: str                     # Text with cues removed
    cues: List[SoundCue]                # Extracted cues
    cue_positions: Dict[int, int]       # Map: cue index -> char position


class CueParser:
    """Parse sound cues from manuscript text."""

    CUE_PATTERN = re.compile(
        r'\[(?P<type>SFX|MUSIC|AMBIANCE|SILENCE):\s*'
        r'(?P<content>[^\]]+)\]'
        r'(?:\s*<!--\s*@(?P<directive>\w+):\s*(?P<params>.+?)\s*-->)?',
        re.IGNORECASE | re.DOTALL
    )

    def parse(self, text: str) -> ParseResult:
        """Parse manuscript and extract all sound cues."""
        cues = []
        cue_positions = {}

        # Track position adjustments as we remove cues
        offset = 0

        for match in self.CUE_PATTERN.finditer(text):
            cue = self._parse_cue(match)
            cue.position_chars = match.start() - offset

            cue_positions[len(cues)] = cue.position_chars
            cues.append(cue)

            # Track how much text we're removing
            offset += match.end() - match.start()

        # Remove cues from text
        clean_text = self.CUE_PATTERN.sub('', text)

        return ParseResult(
            clean_text=clean_text.strip(),
            cues=cues,
            cue_positions=cue_positions,
        )

    def _parse_cue(self, match) -> SoundCue:
        """Parse a single cue match into a SoundCue object."""
        cue_type = CueType(match.group('type').lower())
        content = match.group('content').strip()

        # Parse content (id, command, params)
        parts = content.split()
        cue_id = parts[0] if parts else "unknown"
        command = self._detect_command(parts[1:] if len(parts) > 1 else [])

        # Parse generation hint if present
        generation_hint = None
        if match.group('directive') == 'generate':
            generation_hint = self._parse_generation_hint(
                match.group('params')
            )

        return SoundCue(
            type=cue_type,
            id=cue_id,
            command=command,
            position_chars=0,  # Set by caller
            generation_hint=generation_hint,
            **self._parse_params(parts[1:]),
        )

    def _detect_command(self, parts: List[str]) -> CueCommand:
        """Detect command from cue parts."""
        command_map = {
            'start': CueCommand.START,
            'stop': CueCommand.STOP,
            'fade_in': CueCommand.FADE_IN,
            'fade_out': CueCommand.FADE_OUT,
            'crossfade': CueCommand.CROSSFADE,
            'duck': CueCommand.DUCK,
            'unduck': CueCommand.UNDUCK,
        }

        for part in parts:
            lower = part.lower()
            if lower in command_map:
                return command_map[lower]

        return CueCommand.PLAY  # Default for SFX

    def _parse_params(self, parts: List[str]) -> dict:
        """Parse optional parameters from cue parts."""
        params = {}

        for part in parts:
            # Duration: 5s, 10s, etc.
            if re.match(r'^\d+(\.\d+)?s$', part):
                params['duration_sec'] = float(part[:-1])

            # Volume: -6dB, +3dB, etc.
            elif re.match(r'^[+-]?\d+(\.\d+)?dB$', part, re.IGNORECASE):
                params['volume_db'] = float(part[:-2])

            # Loop flag
            elif part.lower() == 'loop':
                params['loop'] = True

        return params

    def _parse_generation_hint(self, params_str: str) -> dict:
        """Parse generation hint from directive params."""
        # Handle both string prompt and key=value pairs
        if '=' in params_str:
            hint = {}
            for pair in params_str.split(','):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    hint[key.strip()] = value.strip()
            return hint
        else:
            # Plain string prompt
            return {'prompt': params_str.strip().strip('"')}
```

---

### 2. Provider Abstraction (`sound_providers/`)

Abstract base class pattern matching the TTS provider approach.

```
scripts/
└── sound_providers/
    ├── __init__.py
    ├── base.py              # Abstract base classes
    ├── music_suno.py        # Suno music generation
    ├── music_musicgen.py    # MusicGen (local)
    ├── sfx_elevenlabs.py    # ElevenLabs SFX
    ├── sfx_freesound.py     # Freesound library
    └── sfx_stable.py        # Stability Audio
```

**Base Provider Interface** (`base.py`):

```python
"""Abstract base classes for sound providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any


class ProviderType(Enum):
    MUSIC = "music"
    SFX = "sfx"
    AMBIANCE = "ambiance"


@dataclass
class GenerationResult:
    """Result from audio generation."""
    success: bool
    audio_path: Optional[Path] = None
    duration_sec: float = 0.0
    sample_rate: int = 44100
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


class AudioProvider(ABC):
    """Base class for audio generation providers."""

    provider_type: ProviderType
    name: str

    @abstractmethod
    def generate(
        self,
        prompt: str,
        duration_sec: float = 10.0,
        output_path: Optional[Path] = None,
        **kwargs
    ) -> GenerationResult:
        """Generate audio from a text prompt."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is configured and available."""
        pass

    def get_cached(self, cache_key: str) -> Optional[Path]:
        """Check if audio is already cached."""
        # Default implementation - override for custom caching
        return None


class MusicProvider(AudioProvider):
    """Base class for music generation providers."""
    provider_type = ProviderType.MUSIC


class SFXProvider(AudioProvider):
    """Base class for sound effects providers."""
    provider_type = ProviderType.SFX
```

**Suno Provider Example** (`music_suno.py`):

```python
"""Suno AI music generation provider."""

import os
import requests
from pathlib import Path
from typing import Optional
from .base import MusicProvider, GenerationResult


class SunoProvider(MusicProvider):
    """Generate music using Suno AI via third-party API."""

    name = "suno"

    def __init__(self, api_key: str = None, api_base: str = None):
        self.api_key = api_key or os.environ.get("SUNO_API_KEY")
        self.api_base = api_base or os.environ.get(
            "SUNO_API_BASE",
            "https://api.sunoapi.com/v1"
        )

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate(
        self,
        prompt: str,
        duration_sec: float = 60.0,
        output_path: Optional[Path] = None,
        genre: str = None,
        mood: str = None,
        tempo: str = None,
        instrumental: bool = True,
        **kwargs
    ) -> GenerationResult:
        """Generate music from prompt using Suno."""

        if not self.is_available():
            return GenerationResult(
                success=False,
                error="Suno API key not configured"
            )

        # Build generation request
        full_prompt = self._build_prompt(prompt, genre, mood, tempo)

        try:
            response = requests.post(
                f"{self.api_base}/generate",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "prompt": full_prompt,
                    "duration": min(duration_sec, 240),  # Max 4 min
                    "instrumental": instrumental,
                    "model": "suno-v4"
                },
                timeout=120
            )
            response.raise_for_status()

            result = response.json()

            # Download audio
            audio_url = result.get("audio_url")
            if audio_url and output_path:
                self._download_audio(audio_url, output_path)

            return GenerationResult(
                success=True,
                audio_path=output_path,
                duration_sec=result.get("duration", duration_sec),
                metadata={"job_id": result.get("id")}
            )

        except Exception as e:
            return GenerationResult(
                success=False,
                error=str(e)
            )

    def _build_prompt(
        self,
        base: str,
        genre: str = None,
        mood: str = None,
        tempo: str = None
    ) -> str:
        """Build full generation prompt."""
        parts = [base]
        if genre:
            parts.append(f"{genre} style")
        if mood:
            parts.append(f"{mood} mood")
        if tempo:
            parts.append(f"{tempo} tempo")
        return ", ".join(parts)

    def _download_audio(self, url: str, path: Path):
        """Download audio file from URL."""
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(response.content)
```

**Freesound Provider Example** (`sfx_freesound.py`):

```python
"""Freesound library provider for sound effects."""

import os
from pathlib import Path
from typing import Optional
from .base import SFXProvider, GenerationResult


class FreesoundProvider(SFXProvider):
    """Retrieve sound effects from Freesound.org library."""

    name = "freesound"

    def __init__(self, api_key: str = None, cache_dir: Path = None):
        self.api_key = api_key or os.environ.get("FREESOUND_API_KEY")
        self.cache_dir = cache_dir or Path(".sound_cache/freesound")
        self._client = None

    def is_available(self) -> bool:
        return bool(self.api_key)

    @property
    def client(self):
        """Lazy-load Freesound client."""
        if self._client is None:
            import freesound
            self._client = freesound.FreesoundClient()
            self._client.set_token(self.api_key, "token")
        return self._client

    def generate(
        self,
        prompt: str,
        duration_sec: float = 10.0,
        output_path: Optional[Path] = None,
        min_rating: float = 3.5,
        license_filter: str = 'Creative Commons 0',
        **kwargs
    ) -> GenerationResult:
        """Search and download a matching sound effect."""

        if not self.is_available():
            return GenerationResult(
                success=False,
                error="Freesound API key not configured"
            )

        try:
            # Search for matching sounds
            results = self.client.text_search(
                query=prompt,
                filter=f'duration:[0.1 TO {duration_sec * 2}] '
                       f'avg_rating:[{min_rating} TO 5.0] '
                       f'license:"{license_filter}"',
                sort="rating_desc",
                fields="id,name,duration,previews,license"
            )

            if not results or len(list(results)) == 0:
                return GenerationResult(
                    success=False,
                    error=f"No sounds found for: {prompt}"
                )

            # Get first result
            sound = list(results)[0]

            # Download preview (HQ MP3)
            if output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                sound.retrieve_preview(
                    str(output_path.parent),
                    output_path.name
                )

            return GenerationResult(
                success=True,
                audio_path=output_path,
                duration_sec=sound.duration,
                metadata={
                    "freesound_id": sound.id,
                    "name": sound.name,
                    "license": sound.license
                }
            )

        except Exception as e:
            return GenerationResult(
                success=False,
                error=str(e)
            )
```

---

### 3. Asset Resolver (`asset_resolver.py`)

Matches cues to assets via library lookup or generation queue.

```python
"""Resolve sound cues to audio assets."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Any
from .cue_parser import SoundCue, CueType
from .sound_providers.base import AudioProvider, GenerationResult


@dataclass
class ResolvedCue:
    """A cue with its resolved audio asset."""
    cue: SoundCue
    asset_path: Path
    generated: bool = False
    from_cache: bool = False
    metadata: Dict[str, Any] = None


class AssetResolver:
    """Resolve sound cues to audio files."""

    def __init__(
        self,
        library_paths: List[Path],
        cache_dir: Path,
        music_provider: AudioProvider,
        sfx_provider: AudioProvider,
    ):
        self.library_paths = library_paths
        self.cache_dir = cache_dir
        self.music_provider = music_provider
        self.sfx_provider = sfx_provider

        # Build asset index
        self.asset_index = self._build_index()

    def _build_index(self) -> Dict[str, Path]:
        """Index all available audio assets."""
        index = {}
        extensions = {'.wav', '.mp3', '.flac', '.ogg'}

        for lib_path in self.library_paths:
            if not lib_path.exists():
                continue

            for audio_file in lib_path.rglob('*'):
                if audio_file.suffix.lower() in extensions:
                    # Index by filename without extension
                    key = audio_file.stem.lower()
                    index[key] = audio_file

        return index

    def resolve(self, cues: List[SoundCue]) -> List[ResolvedCue]:
        """Resolve all cues to audio assets."""
        resolved = []

        for cue in cues:
            # Skip non-audio cues
            if cue.type == CueType.SILENCE:
                resolved.append(ResolvedCue(
                    cue=cue,
                    asset_path=None,  # Generated at mix time
                ))
                continue

            # Try library lookup first
            asset_path = self._lookup_library(cue.id)

            if asset_path:
                resolved.append(ResolvedCue(
                    cue=cue,
                    asset_path=asset_path,
                    from_cache=True,
                ))
                continue

            # Try cache
            cached = self._lookup_cache(cue)
            if cached:
                resolved.append(ResolvedCue(
                    cue=cue,
                    asset_path=cached,
                    from_cache=True,
                ))
                continue

            # Generate new asset
            result = self._generate(cue)

            if result.success:
                resolved.append(ResolvedCue(
                    cue=cue,
                    asset_path=result.audio_path,
                    generated=True,
                    metadata=result.metadata,
                ))
            else:
                # Mark as unresolved
                resolved.append(ResolvedCue(
                    cue=cue,
                    asset_path=None,
                    metadata={"error": result.error},
                ))

        return resolved

    def _lookup_library(self, cue_id: str) -> Optional[Path]:
        """Look up cue in asset library."""
        key = cue_id.lower().replace('-', '_')
        return self.asset_index.get(key)

    def _lookup_cache(self, cue: SoundCue) -> Optional[Path]:
        """Look up cue in generation cache."""
        cache_key = self._cache_key(cue)
        cache_path = self.cache_dir / f"{cache_key}.wav"

        if cache_path.exists():
            return cache_path
        return None

    def _cache_key(self, cue: SoundCue) -> str:
        """Generate cache key for a cue."""
        parts = [cue.type.value, cue.id]
        if cue.generation_hint:
            # Include hint in cache key
            hint_str = "_".join(
                f"{k}_{v}" for k, v in sorted(cue.generation_hint.items())
            )
            parts.append(hint_str)
        return "_".join(parts)

    def _generate(self, cue: SoundCue) -> GenerationResult:
        """Generate audio for a cue."""
        # Select provider based on cue type
        if cue.type == CueType.MUSIC:
            provider = self.music_provider
        else:
            provider = self.sfx_provider

        # Build prompt
        prompt = self._build_prompt(cue)

        # Generate
        output_path = self.cache_dir / f"{self._cache_key(cue)}.wav"

        return provider.generate(
            prompt=prompt,
            duration_sec=cue.duration_sec or 10.0,
            output_path=output_path,
            **(cue.generation_hint or {})
        )

    def _build_prompt(self, cue: SoundCue) -> str:
        """Build generation prompt from cue."""
        if cue.generation_hint and 'prompt' in cue.generation_hint:
            return cue.generation_hint['prompt']

        # Convert ID to natural language
        # e.g., "door_creak_wooden" -> "wooden door creak"
        words = cue.id.replace('_', ' ').replace('-', ' ')
        return f"{words} sound effect"
```

---

### 4. Audio Mixer (`audio_mixer.py`)

Combines narration with sound layers using timeline-based mixing.

```python
"""Mix narration audio with sound design elements."""

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
import numpy as np

from .cue_parser import SoundCue, CueType, CueCommand
from .asset_resolver import ResolvedCue


@dataclass
class MixConfig:
    """Configuration for audio mixing."""
    # Volume levels (dB relative to narration)
    sfx_volume_db: float = -6.0
    music_volume_db: float = -15.0
    ambiance_volume_db: float = -18.0

    # Ducking parameters
    duck_level_db: float = -24.0
    duck_attack_ms: float = 200.0
    duck_release_ms: float = 800.0
    duck_threshold: float = 0.03

    # Fade defaults
    default_fade_sec: float = 2.0

    # Output
    sample_rate: int = 44100


@dataclass
class TimelineEvent:
    """An audio event on the mix timeline."""
    audio_path: Path
    start_sec: float
    end_sec: Optional[float]
    volume_db: float
    fade_in_sec: float = 0.0
    fade_out_sec: float = 0.0
    loop: bool = False
    duck: bool = True  # Duck under narration


class AudioMixer:
    """Mix narration with sound design elements."""

    def __init__(self, config: MixConfig = None):
        self.config = config or MixConfig()

    def mix(
        self,
        narration_path: Path,
        resolved_cues: List[ResolvedCue],
        output_path: Path,
        char_to_time: callable,  # Function to convert char position to time
    ) -> Path:
        """
        Mix narration with resolved sound cues.

        Args:
            narration_path: Path to narration audio
            resolved_cues: List of resolved cues with assets
            output_path: Path for mixed output
            char_to_time: Function mapping character position to seconds

        Returns:
            Path to mixed audio file
        """
        # Build timeline
        timeline = self._build_timeline(resolved_cues, char_to_time)

        if not timeline:
            # No sound design - return narration as-is
            return narration_path

        # Generate FFmpeg filter graph
        filter_graph = self._build_filter_graph(
            narration_path,
            timeline,
        )

        # Execute mix
        return self._execute_mix(
            narration_path,
            timeline,
            filter_graph,
            output_path,
        )

    def _build_timeline(
        self,
        cues: List[ResolvedCue],
        char_to_time: callable,
    ) -> List[TimelineEvent]:
        """Convert cues to timeline events."""
        events = []
        active_loops = {}  # Track active looping audio

        for rc in cues:
            cue = rc.cue

            # Skip unresolved
            if rc.asset_path is None and cue.type != CueType.SILENCE:
                continue

            start_time = char_to_time(cue.position_chars) + cue.offset_sec

            if cue.type == CueType.SILENCE:
                # Silence is handled in narration, not as an event
                continue

            # Determine volume
            if cue.type == CueType.MUSIC:
                base_volume = self.config.music_volume_db
            elif cue.type == CueType.AMBIANCE:
                base_volume = self.config.ambiance_volume_db
            else:
                base_volume = self.config.sfx_volume_db

            volume = base_volume + cue.volume_db

            # Handle different commands
            if cue.command == CueCommand.PLAY:
                # One-shot sound effect
                events.append(TimelineEvent(
                    audio_path=rc.asset_path,
                    start_sec=start_time,
                    end_sec=start_time + (cue.duration_sec or 10.0),
                    volume_db=volume,
                    duck=cue.type == CueType.SFX,
                ))

            elif cue.command == CueCommand.START:
                # Start continuous audio
                active_loops[cue.id] = TimelineEvent(
                    audio_path=rc.asset_path,
                    start_sec=start_time,
                    end_sec=None,  # Set when stopped
                    volume_db=volume,
                    loop=cue.loop,
                    duck=cue.type != CueType.AMBIANCE,
                )

            elif cue.command in (CueCommand.STOP, CueCommand.FADE_OUT):
                # Stop continuous audio
                if cue.id in active_loops:
                    event = active_loops.pop(cue.id)
                    event.end_sec = start_time
                    if cue.command == CueCommand.FADE_OUT:
                        event.fade_out_sec = cue.fade_duration_sec
                    events.append(event)

            elif cue.command == CueCommand.FADE_IN:
                # Start with fade
                active_loops[cue.id] = TimelineEvent(
                    audio_path=rc.asset_path,
                    start_sec=start_time,
                    end_sec=None,
                    volume_db=volume,
                    fade_in_sec=cue.fade_duration_sec,
                    loop=cue.loop,
                    duck=cue.type != CueType.AMBIANCE,
                )

        # Close any still-active loops at end of audio
        for event in active_loops.values():
            event.end_sec = float('inf')  # Extend to end
            events.append(event)

        return events

    def _build_filter_graph(
        self,
        narration_path: Path,
        timeline: List[TimelineEvent],
    ) -> str:
        """Build FFmpeg filter graph for mixing."""
        # This is a simplified version - full implementation would
        # generate complex filter graphs for ducking, fades, etc.

        filters = []
        inputs = []

        # Input 0 is always narration
        inputs.append(f'-i "{narration_path}"')

        # Add each timeline event as an input
        for i, event in enumerate(timeline):
            inputs.append(f'-i "{event.audio_path}"')

        # Build filter for sidechain compression (ducking)
        # [1:a] music, [0:a] narration (sidechain)
        for i, event in enumerate(timeline):
            input_idx = i + 1

            # Volume adjustment
            volume_filter = f"[{input_idx}:a]volume={event.volume_db}dB"

            # Fade in/out
            if event.fade_in_sec > 0:
                volume_filter += f",afade=t=in:d={event.fade_in_sec}"
            if event.fade_out_sec > 0:
                volume_filter += f",afade=t=out:d={event.fade_out_sec}"

            volume_filter += f"[a{input_idx}]"
            filters.append(volume_filter)

        # Mix with sidechaincompress for ducking
        if timeline:
            mix_inputs = "[0:a]" + "".join(f"[a{i+1}]" for i in range(len(timeline)))
            filters.append(
                f"{mix_inputs}amix=inputs={len(timeline)+1}:duration=first"
                f":dropout_transition=0[mixed]"
            )

        return ";".join(filters)

    def _execute_mix(
        self,
        narration_path: Path,
        timeline: List[TimelineEvent],
        filter_graph: str,
        output_path: Path,
    ) -> Path:
        """Execute FFmpeg mixing command."""

        # Build input list
        inputs = [f'-i "{narration_path}"']
        for event in timeline:
            inputs.append(f'-i "{event.audio_path}"')

        # Build command
        cmd = [
            "ffmpeg", "-y",
            *" ".join(inputs).split(),
            "-filter_complex", filter_graph,
            "-map", "[mixed]" if timeline else "0:a",
            "-c:a", "pcm_s16le",
            "-ar", str(self.config.sample_rate),
            str(output_path)
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg mix failed: {result.stderr}")

        return output_path
```

---

### 5. Pipeline Integration (`batch_produce_with_sound.py`)

Extended pipeline that integrates sound design.

```python
"""
Audiobook production pipeline with sound design.

Extends batch_produce.py with sound cue processing.
"""

from pathlib import Path
from typing import Optional

from .batch_produce import (
    ProductionConfig,
    ProductionReport,
    stage_prep,
    stage_tts,
    stage_master,
    stage_validate,
)
from .cue_parser import CueParser
from .asset_resolver import AssetResolver
from .audio_mixer import AudioMixer, MixConfig
from .sound_providers.music_suno import SunoProvider
from .sound_providers.sfx_elevenlabs import ElevenLabsProvider
from .sound_providers.sfx_freesound import FreesoundProvider


def stage_sound_design(
    config: ProductionConfig,
    report: ProductionReport,
    verbose: bool = False,
) -> None:
    """
    Sound design stage: Parse cues, resolve assets, generate audio.

    Runs after PREP and before TTS.
    """
    if verbose:
        print("\n" + "="*60)
        print("STAGE 1.5: SOUND DESIGN - Processing cues")
        print("="*60)

    # Initialize parser
    parser = CueParser()

    # Initialize providers
    music_provider = SunoProvider()
    sfx_provider = ElevenLabsProvider()
    fallback_sfx = FreesoundProvider()

    # Initialize resolver
    resolver = AssetResolver(
        library_paths=[
            Path("assets/sfx"),
            Path("assets/music"),
            Path("assets/ambiance"),
        ],
        cache_dir=Path(config.output_dir) / ".sound_cache",
        music_provider=music_provider,
        sfx_provider=sfx_provider,
    )

    # Process each chapter
    for chapter in report.chapters:
        if verbose:
            print(f"  Processing cues for Chapter {chapter.number}")

        # Read chapter text
        with open(chapter.text_file, 'r') as f:
            text = f.read()

        # Parse cues
        parse_result = parser.parse(text)

        if verbose:
            print(f"    Found {len(parse_result.cues)} cues")

        # Update chapter text file (cues removed)
        with open(chapter.text_file, 'w') as f:
            f.write(parse_result.clean_text)

        # Resolve assets
        resolved = resolver.resolve(parse_result.cues)

        # Store for mixing stage
        chapter.sound_cues = resolved
        chapter.cue_positions = parse_result.cue_positions

        # Report
        generated = sum(1 for r in resolved if r.generated)
        cached = sum(1 for r in resolved if r.from_cache)
        failed = sum(1 for r in resolved if r.asset_path is None)

        if verbose:
            print(f"    Resolved: {cached} cached, {generated} generated, {failed} failed")


def stage_mix(
    config: ProductionConfig,
    report: ProductionReport,
    verbose: bool = False,
) -> None:
    """
    Mixing stage: Combine TTS output with sound design.

    Runs after TTS and before MASTER.
    """
    if verbose:
        print("\n" + "="*60)
        print("STAGE 3.5: MIX - Combining audio layers")
        print("="*60)

    mixer = AudioMixer(MixConfig())

    for chapter in report.chapters:
        if not hasattr(chapter, 'sound_cues') or not chapter.sound_cues:
            continue

        if not chapter.raw_audio_file:
            continue

        if verbose:
            print(f"  Mixing Chapter {chapter.number}")

        # Calculate character-to-time mapping
        # (simplified - real implementation would use word timestamps from TTS)
        def char_to_time(char_pos: int) -> float:
            # Rough estimate: 15 characters per second of speech
            return char_pos / 15.0

        # Mix
        mixed_path = Path(chapter.raw_audio_file).with_suffix('.mixed.wav')

        mixer.mix(
            narration_path=Path(chapter.raw_audio_file),
            resolved_cues=chapter.sound_cues,
            output_path=mixed_path,
            char_to_time=char_to_time,
        )

        # Update chapter to use mixed audio
        chapter.raw_audio_file = str(mixed_path)

        if verbose:
            print(f"    Mixed to {mixed_path}")


def run_pipeline_with_sound(
    config: ProductionConfig,
    verbose: bool = False,
) -> ProductionReport:
    """Run production pipeline with sound design integration."""

    # Initialize report
    report = ProductionReport(
        title=config.title or Path(config.manuscript_path).stem,
        config={...},
        started_at=datetime.now().isoformat(),
    )

    # Pipeline stages
    stage_prep(config, report, verbose)
    stage_sound_design(config, report, verbose)  # NEW
    stage_tts(config, report, verbose)
    stage_mix(config, report, verbose)           # NEW
    stage_master(config, report, verbose)
    stage_validate(config, report, verbose)

    return report
```

---

## Configuration

### Environment Variables

```bash
# Music Generation
export SUNO_API_KEY="your-suno-api-key"
export SUNO_API_BASE="https://api.sunoapi.com/v1"

# Sound Effects
export ELEVENLABS_API_KEY="your-elevenlabs-key"
export FREESOUND_API_KEY="your-freesound-key"

# Stability Audio (alternative)
export STABILITY_API_KEY="your-stability-key"
```

### Configuration File (`sound_design_config.json`)

```json
{
  "providers": {
    "music": {
      "primary": "suno",
      "fallback": "musicgen",
      "config": {
        "suno": {
          "model": "suno-v4",
          "default_instrumental": true
        },
        "musicgen": {
          "model_size": "large",
          "device": "cuda"
        }
      }
    },
    "sfx": {
      "primary": "elevenlabs",
      "fallback": "freesound",
      "config": {
        "elevenlabs": {
          "model": "eleven_text_to_sound_v2"
        },
        "freesound": {
          "default_license": "Creative Commons 0",
          "min_rating": 3.5
        }
      }
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
  "cache": {
    "enabled": true,
    "directory": ".sound_cache",
    "max_size_mb": 5000
  },
  "assets": {
    "library_paths": [
      "assets/sfx",
      "assets/music",
      "assets/ambiance"
    ]
  }
}
```

---

## Directory Structure

```
StorytellingReferenceBank/
├── scripts/
│   ├── batch_produce.py           # Existing pipeline
│   ├── batch_produce_with_sound.py # Extended pipeline
│   ├── cue_parser.py              # NEW: Sound cue parsing
│   ├── asset_resolver.py          # NEW: Asset resolution
│   ├── audio_mixer.py             # NEW: Timeline mixing
│   └── sound_providers/           # NEW: Provider implementations
│       ├── __init__.py
│       ├── base.py
│       ├── music_suno.py
│       ├── music_musicgen.py
│       ├── sfx_elevenlabs.py
│       ├── sfx_freesound.py
│       └── sfx_stable.py
├── assets/                        # NEW: Sound asset library
│   ├── sfx/
│   ├── music/
│   └── ambiance/
├── audiobook-specs/
│   ├── acx-requirements.md
│   └── sound-design-spec.md       # NEW: Cue format specification
├── docs/
│   ├── sound-design-research.md   # NEW: Tool research
│   └── sound-design-architecture.md # NEW: This document
└── sound_design_config.json       # NEW: Configuration
```

---

## Usage Example

### Manuscript with Sound Cues

```markdown
# Chapter 1: The Storm

[AMBIANCE: forest_night START -15dB]
[MUSIC: suspense_theme FADE_IN 3s -18dB]

The wind howled through the ancient oaks as Sarah made her way along the moonlit path.

[SFX: wind_howl]
[SFX: footsteps_leaves]

A branch snapped somewhere in the darkness.

[SFX: branch_snap]
[SILENCE: beat]

She froze.

[MUSIC: DUCK -24dB]

"Who's there?" she called into the void.

[MUSIC: UNDUCK]
[SFX: owl_hoot OFFSET +0.5s]

Only the owl answered.

[AMBIANCE: FADE_OUT 2s]
[MUSIC: FADE_OUT 3s]
```

### Production Command

```bash
python batch_produce_with_sound.py manuscript.txt \
    --persona personas/narrator.json \
    --output-dir audiobook/ \
    --sound-config sound_design_config.json \
    --verbose
```

### Output

```
STAGE 1: PREP - Splitting manuscript
  Split into 12 chapters
  Total words: 45,230

STAGE 1.5: SOUND DESIGN - Processing cues
  Processing cues for Chapter 1
    Found 8 cues
    Resolved: 3 cached, 4 generated, 1 failed
  Processing cues for Chapter 2
    Found 5 cues
    Resolved: 5 cached, 0 generated, 0 failed
  ...

STAGE 2: TTS - Generating audio
  Using persona: Literary Narrator
  Generating Chapter 1: The Storm
    → audiobook/raw_audio/Chapter_01.wav
  ...

STAGE 3.5: MIX - Combining audio layers
  Mixing Chapter 1
    Mixed to audiobook/raw_audio/Chapter_01.mixed.wav
  ...

STAGE 4: MASTER - Post-processing for ACX
  Processing Chapter 1
    → audiobook/final/Chapter_01.mp3
  ...

STAGE 5: VALIDATE - Checking ACX compliance
  Chapter 1: PASSED
  ...

PRODUCTION COMPLETE
  Chapters: 12
  Total duration: 8.5 hours
  ACX Validation: 12 passed, 0 failed
```

---

## Future Enhancements

1. **Word-Level Timestamps**: Use TTS word timestamps for precise cue alignment
2. **Spatial Audio**: Support for binaural/surround mixing
3. **AI Cue Suggestion**: Automatically suggest sound cues based on manuscript content
4. **Real-Time Preview**: Web interface for previewing sound design
5. **Stem Export**: Export separate stems for professional post-production
6. **Adaptive Music**: Music that responds to narrative pacing
