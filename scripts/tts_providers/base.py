"""
Abstract base class for TTS providers.

All TTS backends must implement this interface to be hot-swappable
in the StorytellingReferenceBank production pipeline.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


class TTSCapability(Enum):
    """Capabilities that a TTS provider may support."""
    VOICE_CLONING = "voice_cloning"           # Clone voice from reference audio
    VOICE_DESIGN = "voice_design"             # Create voice from text description
    STREAMING = "streaming"                    # Stream audio as it's generated
    SSML = "ssml"                              # SSML markup support
    EMOTION_CONTROL = "emotion_control"        # Control emotional expression
    SPEED_CONTROL = "speed_control"            # Adjust speaking rate
    PITCH_CONTROL = "pitch_control"            # Adjust pitch
    MULTILINGUAL = "multilingual"              # Multiple language support
    LONG_FORM = "long_form"                    # Native long-form text handling
    WORD_TIMESTAMPS = "word_timestamps"        # Word-level timing info
    LOCAL = "local"                            # Runs locally (no API)
    CUSTOM_MODELS = "custom_models"            # Support for fine-tuned models


@dataclass
class Voice:
    """Represents an available voice from a provider."""
    id: str
    name: str
    description: Optional[str] = None
    language: Optional[str] = None
    gender: Optional[str] = None
    style: Optional[str] = None
    preview_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TTSResult:
    """Result from TTS generation."""
    audio: Any  # numpy array or bytes depending on provider
    sample_rate: int
    duration_seconds: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_tuple(self) -> Tuple[Any, int]:
        """Return as (waveform, sample_rate) tuple for compatibility."""
        # Wrap in list if needed for legacy compatibility
        if isinstance(self.audio, list):
            return self.audio, self.sample_rate
        return [self.audio], self.sample_rate


@dataclass
class ProviderConfig:
    """Configuration for a TTS provider."""
    # API credentials (for cloud providers)
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None

    # Model settings (for local providers)
    model_path: Optional[str] = None
    model_variant: Optional[str] = None
    device: Optional[str] = None  # "cuda", "cpu", "mps"

    # Generation defaults
    default_language: str = "English"
    default_sample_rate: int = 24000

    # Rate limiting
    max_retries: int = 3
    retry_delay: float = 1.0
    requests_per_minute: Optional[int] = None

    # Caching
    cache_dir: Optional[str] = None
    enable_cache: bool = False

    # Provider-specific options
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProviderConfig":
        """Create config from dictionary."""
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        known = {k: v for k, v in data.items() if k in known_fields and k != 'extra'}
        extra = {k: v for k, v in data.items() if k not in known_fields}
        return cls(**known, extra=extra)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            k: v for k, v in self.__dict__.items()
            if v is not None and k != 'extra'
        }
        result.update(self.extra)
        return result


class TTSProvider(ABC):
    """
    Abstract base class for TTS providers.

    Implementations must provide:
    - generate(): Core text-to-speech generation
    - list_voices(): Available voices
    - get_capabilities(): Provider capabilities

    Optional methods:
    - generate_from_reference(): Voice cloning
    - validate_config(): Configuration validation
    - cleanup(): Resource cleanup
    """

    def __init__(self, config: Optional[Union[ProviderConfig, Dict[str, Any]]] = None):
        """
        Initialize the provider.

        Args:
            config: Provider configuration (ProviderConfig or dict)
        """
        if config is None:
            self.config = ProviderConfig()
        elif isinstance(config, dict):
            self.config = ProviderConfig.from_dict(config)
        else:
            self.config = config

        self._initialized = False

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
        pass

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique provider identifier (e.g., 'qwen', 'elevenlabs')."""
        pass

    @abstractmethod
    def generate(
        self,
        text: str,
        voice: Optional[Union[str, Voice]] = None,
        language: Optional[str] = None,
        output_path: Optional[str] = None,
        **kwargs
    ) -> TTSResult:
        """
        Generate speech from text.

        Args:
            text: Text to synthesize
            voice: Voice ID, Voice object, or voice description
            language: Target language (defaults to config default)
            output_path: If provided, save audio to this path
            **kwargs: Provider-specific options

        Returns:
            TTSResult with generated audio
        """
        pass

    def generate_from_reference(
        self,
        text: str,
        reference_audio: str,
        reference_text: Optional[str] = None,
        output_path: Optional[str] = None,
        **kwargs
    ) -> TTSResult:
        """
        Generate speech using voice cloning from reference audio.

        Args:
            text: Text to synthesize
            reference_audio: Path to reference audio file (3-15 seconds optimal)
            reference_text: Transcript of reference audio (required by some providers)
            output_path: If provided, save audio to this path
            **kwargs: Provider-specific options

        Returns:
            TTSResult with generated audio

        Raises:
            NotImplementedError: If provider doesn't support voice cloning
        """
        raise NotImplementedError(
            f"{self.name} does not support voice cloning. "
            f"Supported capabilities: {[c.value for c in self.get_capabilities()]}"
        )

    @abstractmethod
    def list_voices(self, language: Optional[str] = None) -> List[Voice]:
        """
        List available voices.

        Args:
            language: Filter by language (optional)

        Returns:
            List of available Voice objects
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> List[TTSCapability]:
        """
        Get provider capabilities.

        Returns:
            List of supported TTSCapability values
        """
        pass

    def supports(self, capability: TTSCapability) -> bool:
        """Check if provider supports a specific capability."""
        return capability in self.get_capabilities()

    def validate_config(self) -> Tuple[bool, Optional[str]]:
        """
        Validate provider configuration.

        Returns:
            Tuple of (is_valid, error_message)
        """
        return True, None

    def initialize(self) -> None:
        """
        Initialize the provider (load models, authenticate, etc.).

        Called lazily on first use or explicitly by user.
        """
        if self._initialized:
            return

        valid, error = self.validate_config()
        if not valid:
            raise ValueError(f"Invalid configuration: {error}")

        self._do_initialize()
        self._initialized = True

    def _do_initialize(self) -> None:
        """Provider-specific initialization. Override in subclasses."""
        pass

    def cleanup(self) -> None:
        """Clean up provider resources (unload models, close connections)."""
        self._initialized = False

    def save_audio(
        self,
        result: TTSResult,
        output_path: str,
        normalize: bool = True
    ) -> None:
        """
        Save TTSResult to audio file.

        Args:
            result: TTSResult to save
            output_path: Output file path
            normalize: Normalize audio levels
        """
        try:
            import soundfile as sf
            import numpy as np
        except ImportError as e:
            raise ImportError(
                "Missing dependencies. Install with: pip install soundfile numpy"
            ) from e

        # Extract audio array
        audio = result.audio
        if isinstance(audio, list):
            audio = audio[0]
        if hasattr(audio, 'cpu'):
            audio = audio.cpu().numpy()

        # Normalize if requested
        if normalize:
            max_val = np.abs(audio).max()
            if max_val > 0:
                audio = audio / max_val * 0.95

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        sf.write(output_path, audio, result.sample_rate)

    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
        return False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(provider_id='{self.provider_id}')"
