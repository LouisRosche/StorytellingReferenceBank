"""
TTS Provider Abstraction Layer for StorytellingReferenceBank.

This module provides a hot-swappable TTS backend system. Any TTS provider
can be used as long as it implements the TTSProvider interface.

Quick Start:
    from tts_providers import get_provider, TTSCapability

    # Get the default provider (Qwen)
    provider = get_provider()

    # Or specify a provider
    provider = get_provider("kokoro")

    # Generate speech
    result = provider.generate(
        text="Hello, world!",
        voice="narrator_warm",
    )

    # Save to file
    provider.save_audio(result, "output.wav")

Available Providers:
    - qwen: Local Qwen3-TTS model (default, full-featured)
    - kokoro: Local Kokoro TTS model (lightweight, fast)

Adding Custom Providers:
    1. Create a class that inherits from TTSProvider
    2. Implement required methods: generate(), list_voices(), get_capabilities()
    3. Register with register_provider()

See README.md in this directory for detailed documentation.
"""

from typing import Any, Dict, Optional, Type, Union

# Core interfaces
from .base import (
    TTSProvider,
    TTSCapability,
    TTSResult,
    ProviderConfig,
    Voice,
)

# Provider implementations
from .qwen_provider import QwenTTSProvider
from .kokoro_provider import KokoroTTSProvider


# Registry of available providers
_PROVIDERS: Dict[str, Type[TTSProvider]] = {
    "qwen": QwenTTSProvider,
    "kokoro": KokoroTTSProvider,
}

# Default provider
_DEFAULT_PROVIDER = "qwen"


def register_provider(provider_id: str, provider_class: Type[TTSProvider]) -> None:
    """
    Register a custom TTS provider.

    Args:
        provider_id: Unique identifier for the provider
        provider_class: Class that inherits from TTSProvider

    Example:
        from tts_providers import register_provider, TTSProvider

        class MyCustomProvider(TTSProvider):
            ...

        register_provider("custom", MyCustomProvider)
    """
    if not issubclass(provider_class, TTSProvider):
        raise TypeError(f"Provider must inherit from TTSProvider, got {type(provider_class)}")
    _PROVIDERS[provider_id] = provider_class


def get_provider(
    provider_id: Optional[str] = None,
    config: Optional[Union[ProviderConfig, Dict[str, Any]]] = None,
    **kwargs
) -> TTSProvider:
    """
    Get a TTS provider instance.

    Args:
        provider_id: Provider identifier (default: "qwen")
            Available: "qwen", "kokoro"
        config: Provider configuration (ProviderConfig or dict)
        **kwargs: Additional config options merged into config dict

    Returns:
        Configured TTSProvider instance

    Example:
        # Default provider
        provider = get_provider()

        # With full config
        provider = get_provider("qwen", {
            "model_variant": "1.7B-VoiceDesign",
            "device": "cuda",
        })
    """
    provider_id = provider_id or _DEFAULT_PROVIDER

    if provider_id not in _PROVIDERS:
        available = list(_PROVIDERS.keys())
        raise ValueError(
            f"Unknown provider: {provider_id}. Available providers: {available}"
        )

    # Build config
    if config is None:
        config = ProviderConfig.from_dict(kwargs)
    elif isinstance(config, dict):
        merged = {**config, **kwargs}
        config = ProviderConfig.from_dict(merged)
    elif kwargs:
        # Merge kwargs into existing config
        config_dict = config.to_dict()
        config_dict.update(kwargs)
        config = ProviderConfig.from_dict(config_dict)

    provider_class = _PROVIDERS[provider_id]
    return provider_class(config)


def list_providers() -> Dict[str, str]:
    """
    List available TTS providers.

    Returns:
        Dict mapping provider IDs to provider names
    """
    result = {}
    for provider_id, provider_class in _PROVIDERS.items():
        try:
            temp = provider_class.__new__(provider_class)
            temp.config = ProviderConfig()
            result[provider_id] = temp.name
        except Exception:
            result[provider_id] = provider_class.__name__
    return result


def get_default_provider() -> str:
    """Get the default provider ID."""
    return _DEFAULT_PROVIDER


def set_default_provider(provider_id: str) -> None:
    """
    Set the default provider.

    Args:
        provider_id: Provider identifier to use as default
    """
    global _DEFAULT_PROVIDER
    if provider_id not in _PROVIDERS:
        raise ValueError(f"Unknown provider: {provider_id}")
    _DEFAULT_PROVIDER = provider_id


# Convenience function for common use case
def generate_speech(
    text: str,
    voice: Optional[str] = None,
    provider: Optional[str] = None,
    output_path: Optional[str] = None,
    **kwargs
) -> TTSResult:
    """
    Generate speech using the default or specified provider.

    Args:
        text: Text to synthesize
        voice: Voice ID or description
        provider: Provider ID (default: "qwen")
        output_path: Optional output file path
        **kwargs: Additional options passed to generate()

    Returns:
        TTSResult with generated audio
    """
    tts = get_provider(provider)
    return tts.generate(
        text=text,
        voice=voice,
        output_path=output_path,
        **kwargs
    )


__all__ = [
    # Core interfaces
    "TTSProvider",
    "TTSCapability",
    "TTSResult",
    "ProviderConfig",
    "Voice",

    # Provider implementations
    "QwenTTSProvider",
    "KokoroTTSProvider",

    # Factory functions
    "get_provider",
    "register_provider",
    "list_providers",
    "get_default_provider",
    "set_default_provider",
    "generate_speech",
]
