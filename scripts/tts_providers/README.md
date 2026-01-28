# TTS Provider Abstraction Layer

Hot-swappable TTS backend system for StorytellingReferenceBank audiobook production.

## Overview

This module provides a unified interface for multiple TTS providers, allowing you to:
- Switch between TTS backends without code changes
- Use local models (Qwen, Coqui) or cloud APIs (ElevenLabs, OpenAI)
- Mix providers for different use cases (e.g., cloning vs. preset voices)

## Quick Start

```python
from tts_providers import get_provider

# Use default provider (Qwen)
provider = get_provider()
result = provider.generate("Hello, world!", voice="A warm narrator voice")
provider.save_audio(result, "output.wav")

# Use a specific provider
provider = get_provider("elevenlabs", api_key="your-api-key")
result = provider.generate("Hello, world!", voice="Rachel")
```

## Available Providers

| Provider | ID | Type | Voice Cloning | Voice Design | Requirements |
|----------|-----|------|---------------|--------------|--------------|
| Qwen3-TTS | `qwen` | Local | Yes | Yes | GPU recommended, `pip install qwen-tts torch` |
| ElevenLabs | `elevenlabs` | Cloud | Yes | Yes | API key, `pip install elevenlabs` |
| OpenAI TTS | `openai` | Cloud | No | No | API key, `pip install openai` |
| Coqui/XTTS | `coqui` | Local | Yes* | No | GPU recommended, `pip install TTS` |

*Coqui voice cloning requires XTTS model

## Provider Capabilities

```python
from tts_providers import get_provider, TTSCapability

provider = get_provider("qwen")

# Check specific capability
if provider.supports(TTSCapability.VOICE_CLONING):
    result = provider.generate_from_reference(
        text="Clone this voice",
        reference_audio="sample.wav",
        reference_text="Transcript of the sample"
    )

# List all capabilities
capabilities = provider.get_capabilities()
# [TTSCapability.VOICE_CLONING, TTSCapability.VOICE_DESIGN, ...]
```

### Capability Reference

| Capability | Description |
|------------|-------------|
| `VOICE_CLONING` | Clone voice from reference audio |
| `VOICE_DESIGN` | Create voice from text description |
| `STREAMING` | Stream audio as it's generated |
| `SSML` | SSML markup support |
| `EMOTION_CONTROL` | Control emotional expression |
| `SPEED_CONTROL` | Adjust speaking rate |
| `PITCH_CONTROL` | Adjust pitch |
| `MULTILINGUAL` | Multiple language support |
| `LONG_FORM` | Native long-form text handling |
| `WORD_TIMESTAMPS` | Word-level timing info |
| `LOCAL` | Runs locally (no API) |
| `CUSTOM_MODELS` | Support for fine-tuned models |

## Provider Configuration

### Qwen3-TTS (Default)

```python
provider = get_provider("qwen", {
    "model_variant": "1.7B-VoiceDesign",  # or "1.7B-Base", "0.6B"
    "device": "cuda",  # or "cpu"
    "extra": {
        "use_flash_attention": True,
    }
})

# Voice design (natural language)
result = provider.generate(
    text="Your text here",
    voice="A warm, friendly narrator with moderate pace",
    language="English"
)

# Voice cloning
result = provider.generate_from_reference(
    text="Your text here",
    reference_audio="speaker_sample.wav",
    reference_text="Transcript of the sample audio"
)
```

**Model Variants:**
- `1.7B-Base`: General purpose, good for voice cloning
- `1.7B-VoiceDesign`: Optimized for natural language voice descriptions
- `1.7B-CustomVoice`: For custom fine-tuned voices
- `0.6B`: Smaller, faster model

### ElevenLabs

```python
provider = get_provider("elevenlabs", {
    "api_key": "your-api-key",  # or set ELEVENLABS_API_KEY env var
    "extra": {
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
        }
    }
})

# List available voices
voices = provider.list_voices()
for v in voices:
    print(f"{v.id}: {v.name}")

# Generate with preset voice
result = provider.generate(text="Hello!", voice="Rachel")

# Voice cloning
result = provider.generate_from_reference(
    text="Clone this voice",
    reference_audio="sample.wav"
)
```

### OpenAI TTS

```python
provider = get_provider("openai", {
    "api_key": "your-api-key",  # or set OPENAI_API_KEY env var
    "extra": {
        "model": "tts-1-hd",  # or "tts-1" for faster
        "default_voice": "nova",
    }
})

# Available voices: alloy, echo, fable, onyx, nova, shimmer
result = provider.generate(
    text="Hello!",
    voice="nova",
    speed=1.0,  # 0.25 to 4.0
)
```

### Coqui/XTTS

```python
# Default XTTS v2 model
provider = get_provider("coqui")

# Specific model
provider = get_provider("coqui", {
    "extra": {
        "model_name": "xtts_v2",  # or "vits_ljspeech", etc.
    }
})

# Custom model path
provider = get_provider("coqui", {
    "model_path": "/path/to/my/model",
    "device": "cuda",
})

# Voice cloning with XTTS
result = provider.generate_from_reference(
    text="Clone this voice",
    reference_audio="sample.wav",
    language="en"
)
```

## Adding a New Provider

1. Create a new file in `tts_providers/`:

```python
# tts_providers/my_provider.py
from .base import TTSProvider, TTSCapability, TTSResult, Voice

class MyTTSProvider(TTSProvider):
    @property
    def name(self) -> str:
        return "My TTS Provider"

    @property
    def provider_id(self) -> str:
        return "mytts"

    def generate(self, text, voice=None, language=None, output_path=None, **kwargs):
        # Your implementation here
        ...
        return TTSResult(audio=audio_array, sample_rate=24000, duration_seconds=duration)

    def list_voices(self, language=None):
        return [
            Voice(id="voice1", name="Voice 1", description="..."),
            Voice(id="voice2", name="Voice 2", description="..."),
        ]

    def get_capabilities(self):
        return [TTSCapability.MULTILINGUAL, TTSCapability.LOCAL]

    # Optional: voice cloning
    def generate_from_reference(self, text, reference_audio, reference_text=None, **kwargs):
        ...
```

2. Register the provider:

```python
from tts_providers import register_provider
from tts_providers.my_provider import MyTTSProvider

register_provider("mytts", MyTTSProvider)

# Now use it
provider = get_provider("mytts")
```

3. Or add to `__init__.py` for permanent inclusion:

```python
from .my_provider import MyTTSProvider

_PROVIDERS["mytts"] = MyTTSProvider

__all__.append("MyTTSProvider")
```

## Interface Reference

### TTSProvider (Abstract Base Class)

```python
class TTSProvider(ABC):
    # Required properties
    @property
    def name(self) -> str: ...
    @property
    def provider_id(self) -> str: ...

    # Required methods
    def generate(self, text, voice=None, language=None, output_path=None, **kwargs) -> TTSResult: ...
    def list_voices(self, language=None) -> List[Voice]: ...
    def get_capabilities(self) -> List[TTSCapability]: ...

    # Optional methods (default implementations provided)
    def generate_from_reference(self, text, reference_audio, reference_text=None, **kwargs) -> TTSResult: ...
    def validate_config(self) -> Tuple[bool, Optional[str]]: ...
    def initialize(self) -> None: ...
    def cleanup(self) -> None: ...
    def save_audio(self, result, output_path, normalize=True) -> None: ...

    # Utility methods
    def supports(self, capability: TTSCapability) -> bool: ...
```

### TTSResult

```python
@dataclass
class TTSResult:
    audio: Any              # numpy array
    sample_rate: int        # e.g., 24000
    duration_seconds: float
    metadata: Dict[str, Any]

    def to_tuple(self) -> Tuple[Any, int]:
        """Return (waveform, sample_rate) for legacy compatibility."""
```

### Voice

```python
@dataclass
class Voice:
    id: str
    name: str
    description: Optional[str]
    language: Optional[str]
    gender: Optional[str]
    style: Optional[str]
    preview_url: Optional[str]
    metadata: Dict[str, Any]
```

### ProviderConfig

```python
@dataclass
class ProviderConfig:
    api_key: Optional[str]         # For cloud providers
    api_base_url: Optional[str]
    model_path: Optional[str]      # For local providers
    model_variant: Optional[str]
    device: Optional[str]          # "cuda", "cpu", "mps"
    default_language: str          # Default: "English"
    default_sample_rate: int       # Default: 24000
    max_retries: int               # Default: 3
    retry_delay: float             # Default: 1.0
    cache_dir: Optional[str]
    enable_cache: bool             # Default: False
    extra: Dict[str, Any]          # Provider-specific options
```

## Migration from Direct Qwen Usage

If you're migrating from direct `tts_generator.py` usage:

```python
# Old way
from tts_generator import Persona, generate_from_persona, save_audio
persona = Persona.from_json("persona.json")
wavs, sr = generate_from_persona("Hello!", persona)
save_audio(wavs, sr, "output.wav")

# New way (backward compatible)
from tts_generator import Persona, generate_from_persona, save_audio
# Same code works! tts_generator now uses providers internally

# Or use providers directly
from tts_providers import get_provider
provider = get_provider()
result = provider.generate("Hello!", voice=persona.voice_prompt)
provider.save_audio(result, "output.wav")
```

## Best Practices

1. **Use context managers** for automatic cleanup:
   ```python
   with get_provider("qwen") as provider:
       result = provider.generate("Hello!")
   # Model automatically unloaded
   ```

2. **Check capabilities** before using features:
   ```python
   if provider.supports(TTSCapability.VOICE_CLONING):
       result = provider.generate_from_reference(...)
   else:
       result = provider.generate(...)
   ```

3. **Handle long text** appropriately:
   ```python
   # Providers handle chunking differently
   # For manual control, use the chunking from tts_generator
   from tts_generator import chunk_text
   chunks = chunk_text(long_text, max_chars=2000)
   ```

4. **Cache provider instances** when generating multiple files:
   ```python
   provider = get_provider("qwen")
   provider.initialize()  # Load model once

   for text in texts:
       result = provider.generate(text)
       ...

   provider.cleanup()  # Unload when done
   ```

## Troubleshooting

### "Missing dependency" errors
Install the required package for your provider:
```bash
pip install qwen-tts torch      # For Qwen
pip install elevenlabs          # For ElevenLabs
pip install openai              # For OpenAI
pip install TTS                 # For Coqui
```

### "API key required" errors
Set the API key in config or environment:
```bash
export ELEVENLABS_API_KEY="your-key"
export OPENAI_API_KEY="your-key"
```

### GPU memory issues
Use cleanup() or context managers:
```python
provider = get_provider("qwen")
try:
    result = provider.generate(...)
finally:
    provider.cleanup()  # Frees GPU memory
```

### Provider not found
Check available providers:
```python
from tts_providers import list_providers
print(list_providers())
# {'qwen': 'Qwen3-TTS', 'elevenlabs': 'ElevenLabs', ...}
```
