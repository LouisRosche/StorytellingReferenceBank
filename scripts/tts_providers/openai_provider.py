"""
OpenAI TTS provider implementation.

Cloud-based TTS using OpenAI's text-to-speech API.

API Documentation: https://platform.openai.com/docs/guides/text-to-speech
"""

import os
from typing import Any, Dict, List, Optional, Tuple, Union

from .base import (
    TTSProvider,
    TTSCapability,
    TTSResult,
    ProviderConfig,
    Voice,
)


class OpenAITTSProvider(TTSProvider):
    """
    OpenAI TTS provider for cloud-based voice synthesis.

    STATUS: EXPERIMENTAL — generate() is not yet implemented and will raise
    NotImplementedError. Voice cloning is not supported by OpenAI's API.
    Use Qwen or Kokoro providers for production workloads.

    Supports (when implemented):
    - Six preset voices with distinct characteristics
    - Two quality levels (tts-1 for speed, tts-1-hd for quality)
    - Speed adjustment (0.25x to 4.0x)
    - Multiple output formats

    Available voices:
    - alloy: Neutral, balanced
    - echo: Male, warm
    - fable: British, expressive
    - onyx: Deep, authoritative
    - nova: Female, friendly
    - shimmer: Female, soft

    Configuration:
        api_key: OpenAI API key (or OPENAI_API_KEY env var)
        model: Model to use ("tts-1" or "tts-1-hd")
        default_voice: Default voice ID
        response_format: Audio format (mp3, opus, aac, flac, wav, pcm)

    Example:
        provider = OpenAITTSProvider({
            "api_key": "your-api-key",
            "extra": {
                "model": "tts-1-hd",
                "default_voice": "nova",
            }
        })
    """

    # Available voices with descriptions
    VOICES = {
        "alloy": {
            "name": "Alloy",
            "description": "Neutral and balanced voice, versatile for many applications",
            "gender": None,
        },
        "echo": {
            "name": "Echo",
            "description": "Warm male voice with a friendly tone",
            "gender": "male",
        },
        "fable": {
            "name": "Fable",
            "description": "British-accented voice, expressive and engaging",
            "gender": None,
        },
        "onyx": {
            "name": "Onyx",
            "description": "Deep and authoritative voice, good for narration",
            "gender": "male",
        },
        "nova": {
            "name": "Nova",
            "description": "Friendly female voice with clear articulation",
            "gender": "female",
        },
        "shimmer": {
            "name": "Shimmer",
            "description": "Soft female voice, gentle and calm",
            "gender": "female",
        },
    }

    # Available models
    MODELS = {
        "tts-1": "Standard quality, faster generation",
        "tts-1-hd": "High definition quality, slower generation",
    }

    # Supported output formats
    FORMATS = ["mp3", "opus", "aac", "flac", "wav", "pcm"]

    def __init__(self, config: Optional[Union[ProviderConfig, Dict[str, Any]]] = None):
        super().__init__(config)
        self._client = None

    @property
    def name(self) -> str:
        return "OpenAI TTS"

    @property
    def provider_id(self) -> str:
        return "openai"

    def _get_api_key(self) -> str:
        """Get API key from config or environment."""
        return self.config.api_key or os.environ.get("OPENAI_API_KEY", "")

    def _get_client(self):
        """Get or create OpenAI client."""
        if self._client is not None:
            return self._client

        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "OpenAI SDK not installed. Install with: pip install openai"
            )

        api_key = self._get_api_key()
        if not api_key:
            raise ValueError(
                "OpenAI API key required. Set api_key in config or "
                "OPENAI_API_KEY environment variable."
            )

        self._client = OpenAI(api_key=api_key)
        return self._client

    def _do_initialize(self) -> None:
        """Initialize the OpenAI client."""
        self._get_client()

    def generate(
        self,
        text: str,
        voice: Optional[Union[str, Voice]] = None,
        language: Optional[str] = None,
        output_path: Optional[str] = None,
        **kwargs
    ) -> TTSResult:
        """
        Generate speech using OpenAI TTS API.

        Args:
            text: Text to synthesize (max 4096 characters per request)
            voice: Voice ID ("alloy", "echo", "fable", "onyx", "nova", "shimmer")
            language: Not used (model auto-detects language)
            output_path: Optional output file path
            **kwargs:
                model: "tts-1" or "tts-1-hd" (default: config or "tts-1")
                speed: Playback speed 0.25-4.0 (default: 1.0)
                response_format: Output format (default: "mp3")

        Returns:
            TTSResult with generated audio
        """
        self.initialize()

        # Resolve voice ID
        if isinstance(voice, Voice):
            voice_id = voice.id
        elif voice:
            voice_id = voice
        else:
            voice_id = self.config.extra.get("default_voice", "nova")

        if voice_id not in self.VOICES:
            raise ValueError(
                f"Unknown voice: {voice_id}. "
                f"Available voices: {list(self.VOICES.keys())}"
            )

        model = kwargs.get("model", self.config.extra.get("model", "tts-1"))
        speed = kwargs.get("speed", 1.0)
        response_format = kwargs.get(
            "response_format",
            self.config.extra.get("response_format", "mp3")
        )

        if model not in self.MODELS:
            raise ValueError(f"Unknown model: {model}. Available: {list(self.MODELS.keys())}")

        if not 0.25 <= speed <= 4.0:
            raise ValueError(f"Speed must be between 0.25 and 4.0, got {speed}")

        if response_format not in self.FORMATS:
            raise ValueError(
                f"Unknown format: {response_format}. Available: {self.FORMATS}"
            )

        # This would make the actual API call
        raise NotImplementedError(
            "OpenAI TTS API integration not yet implemented. "
            f"To implement: use self._client.audio.speech.create() "
            f"with model={model}, voice={voice_id}"
        )

        # Implementation would look like:
        # response = self._client.audio.speech.create(
        #     model=model,
        #     voice=voice_id,
        #     input=text,
        #     speed=speed,
        #     response_format=response_format,
        # )
        #
        # # Save to temp file or output path
        # import tempfile
        # import soundfile as sf
        # import numpy as np
        #
        # if output_path:
        #     response.write_to_file(output_path)
        #     audio_path = output_path
        # else:
        #     with tempfile.NamedTemporaryFile(suffix=f".{response_format}", delete=False) as f:
        #         response.write_to_file(f.name)
        #         audio_path = f.name
        #
        # # Load audio for result
        # audio, sr = sf.read(audio_path)
        # duration = len(audio) / sr
        #
        # return TTSResult(
        #     audio=audio,
        #     sample_rate=sr,
        #     duration_seconds=duration,
        #     metadata={
        #         "voice": voice_id,
        #         "model": model,
        #         "speed": speed,
        #     }
        # )

    def generate_from_reference(
        self,
        text: str,
        reference_audio: str,
        reference_text: Optional[str] = None,
        output_path: Optional[str] = None,
        **kwargs
    ) -> TTSResult:
        """
        Voice cloning is not supported by OpenAI TTS.

        Raises:
            NotImplementedError: Always, as OpenAI doesn't support cloning
        """
        raise NotImplementedError(
            "OpenAI TTS does not support voice cloning. "
            "Use a preset voice with generate() instead, or use a different "
            "provider like ElevenLabs or Qwen for voice cloning."
        )

    def list_voices(self, language: Optional[str] = None) -> List[Voice]:
        """
        List available OpenAI voices.

        Args:
            language: Ignored (OpenAI voices work across languages)

        Returns:
            List of available Voice objects
        """
        # OpenAI voices are hardcoded, no API call needed
        voices = []
        for voice_id, info in self.VOICES.items():
            voices.append(Voice(
                id=voice_id,
                name=info["name"],
                description=info["description"],
                gender=info["gender"],
                language=None,  # OpenAI voices are multilingual
            ))
        return voices

    def get_capabilities(self) -> List[TTSCapability]:
        """Get OpenAI TTS capabilities."""
        return [
            TTSCapability.SPEED_CONTROL,
            TTSCapability.MULTILINGUAL,
        ]

    def validate_config(self) -> Tuple[bool, Optional[str]]:
        """Validate configuration."""
        if not self._get_api_key():
            return False, (
                "API key required. Set api_key in config or "
                "OPENAI_API_KEY environment variable."
            )

        model = self.config.extra.get("model")
        if model and model not in self.MODELS:
            return False, f"Unknown model: {model}. Available: {list(self.MODELS.keys())}"

        voice = self.config.extra.get("default_voice")
        if voice and voice not in self.VOICES:
            return False, f"Unknown voice: {voice}. Available: {list(self.VOICES.keys())}"

        return True, None

    def cleanup(self) -> None:
        """Clean up resources."""
        self._client = None
        super().cleanup()

    def get_character_limit(self) -> int:
        """Get maximum characters per request."""
        return 4096

    def chunk_text_for_api(self, text: str) -> List[str]:
        """
        Split text into chunks that fit within API limits.

        Args:
            text: Full text to split

        Returns:
            List of text chunks
        """
        import re

        max_chars = self.get_character_limit()

        if len(text) <= max_chars:
            return [text]

        # Split on sentence boundaries
        sentence_pattern = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_pattern, text)

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 <= max_chars:
                current_chunk = f"{current_chunk} {sentence}".strip()
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk)

        return chunks
