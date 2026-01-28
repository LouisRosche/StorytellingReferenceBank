"""
Qwen3-TTS provider implementation.

Wraps the local Qwen3-TTS model for audiobook production.
Supports both voice design (natural language prompts) and voice cloning.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .base import (
    TTSProvider,
    TTSCapability,
    TTSResult,
    ProviderConfig,
    Voice,
)

# Model variants mapping
QWEN_VARIANTS = {
    "1.7B-Base": "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
    "1.7B-VoiceDesign": "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
    "1.7B-CustomVoice": "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
    "0.6B": "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
}


class QwenTTSProvider(TTSProvider):
    """
    Qwen3-TTS provider for local TTS generation.

    Supports:
    - Voice design: Create voices from natural language descriptions
    - Voice cloning: Clone voices from reference audio
    - Long-form text with automatic chunking

    Model variants:
    - 1.7B-Base: General purpose, good for voice cloning
    - 1.7B-VoiceDesign: Optimized for natural language voice descriptions
    - 1.7B-CustomVoice: For custom fine-tuned voices
    - 0.6B: Smaller, faster model

    Configuration:
        model_variant: Model variant to use (default: "1.7B-Base")
        device: Device to run on ("cuda", "cpu", "mps")
        use_flash_attention: Enable flash attention if available
    """

    def __init__(self, config: Optional[Union[ProviderConfig, Dict[str, Any]]] = None):
        super().__init__(config)
        self._model = None
        self._model_name = None

    @property
    def name(self) -> str:
        return "Qwen3-TTS"

    @property
    def provider_id(self) -> str:
        return "qwen"

    def _do_initialize(self) -> None:
        """Load the Qwen3-TTS model."""
        self._load_model(self.config.model_variant or "1.7B-Base")

    def _load_model(self, variant: str):
        """
        Load or switch Qwen3-TTS model.

        Args:
            variant: Model variant key
        """
        model_name = QWEN_VARIANTS.get(variant, QWEN_VARIANTS["1.7B-Base"])

        if self._model is not None and self._model_name == model_name:
            return self._model

        try:
            import torch
            from qwen_tts import Qwen3TTSModel
        except ImportError as e:
            raise ImportError(
                "Missing dependency. Install with: pip install qwen-tts torch"
            ) from e

        print(f"Loading model: {model_name}...", file=sys.stderr)

        # Determine device
        if self.config.device:
            device = self.config.device
        elif torch.cuda.is_available():
            device = "cuda:0"
        else:
            device = "cpu"

        dtype = torch.bfloat16 if "cuda" in device else torch.float32

        # Try flash attention if available
        use_flash = self.config.extra.get("use_flash_attention", True)
        if use_flash:
            try:
                self._model = Qwen3TTSModel.from_pretrained(
                    model_name,
                    device_map=device,
                    dtype=dtype,
                    attn_implementation="flash_attention_2"
                )
            except Exception:
                use_flash = False

        if not use_flash or self._model is None:
            self._model = Qwen3TTSModel.from_pretrained(
                model_name,
                device_map=device,
                dtype=dtype,
            )

        self._model_name = model_name
        print(f"Model loaded on {device}", file=sys.stderr)
        return self._model

    def generate(
        self,
        text: str,
        voice: Optional[Union[str, Voice]] = None,
        language: Optional[str] = None,
        output_path: Optional[str] = None,
        **kwargs
    ) -> TTSResult:
        """
        Generate speech using voice design (natural language prompt).

        Args:
            text: Text to synthesize
            voice: Voice description (natural language prompt) or Voice object
            language: Target language
            output_path: Optional output file path
            **kwargs:
                model_variant: Override model variant for this call

        Returns:
            TTSResult with generated audio
        """
        self.initialize()

        language = language or self.config.default_language

        # Get voice prompt
        if isinstance(voice, Voice):
            voice_prompt = voice.description or voice.name
        elif voice:
            voice_prompt = voice
        else:
            voice_prompt = "A neutral, clear narrator voice."

        # Get model variant
        variant = kwargs.get("model_variant", self.config.model_variant)
        if not variant or variant == "1.7B-Base":
            variant = "1.7B-VoiceDesign"

        # Load appropriate model
        model = self._load_model(variant)

        # Generate
        wavs, sr = model.generate_voice_design(
            text=text,
            language=language,
            instruct=voice_prompt,
        )

        # Create result
        audio = wavs[0] if isinstance(wavs, list) else wavs
        if hasattr(audio, 'cpu'):
            audio = audio.cpu().numpy()

        duration = len(audio) / sr

        result = TTSResult(
            audio=audio,
            sample_rate=sr,
            duration_seconds=duration,
            metadata={
                "voice_prompt": voice_prompt,
                "language": language,
                "model": self._model_name,
            }
        )

        if output_path:
            self.save_audio(result, output_path)

        return result

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
            reference_audio: Path to reference audio (3-15 seconds optimal)
            reference_text: Transcript of reference audio (required)
            output_path: Optional output file path
            **kwargs:
                model_variant: Override model variant
                language: Target language

        Returns:
            TTSResult with generated audio

        Raises:
            ValueError: If reference_text not provided
        """
        self.initialize()

        if not reference_text:
            raise ValueError(
                "Qwen3-TTS voice cloning requires reference_text (transcript)"
            )

        language = kwargs.get("language", self.config.default_language)
        variant = kwargs.get("model_variant", self.config.model_variant or "1.7B-Base")

        # Load model
        model = self._load_model(variant)

        # Generate
        wavs, sr = model.generate_voice_clone(
            text=text,
            language=language,
            ref_audio=reference_audio,
            ref_text=reference_text,
        )

        # Create result
        audio = wavs[0] if isinstance(wavs, list) else wavs
        if hasattr(audio, 'cpu'):
            audio = audio.cpu().numpy()

        duration = len(audio) / sr

        result = TTSResult(
            audio=audio,
            sample_rate=sr,
            duration_seconds=duration,
            metadata={
                "reference_audio": reference_audio,
                "language": language,
                "model": self._model_name,
            }
        )

        if output_path:
            self.save_audio(result, output_path)

        return result

    def list_voices(self, language: Optional[str] = None) -> List[Voice]:
        """
        List available voice presets.

        Note: Qwen3-TTS uses voice design (natural language prompts) rather
        than preset voices, so this returns example voice descriptions.
        """
        # Qwen uses voice design, not preset voices
        # Return example voice descriptions as guidance
        voices = [
            Voice(
                id="narrator_neutral",
                name="Neutral Narrator",
                description="A clear, neutral narrator voice with moderate pace.",
                language="English",
            ),
            Voice(
                id="narrator_warm",
                name="Warm Narrator",
                description="A warm, friendly narrator with gentle intonation.",
                language="English",
            ),
            Voice(
                id="narrator_dramatic",
                name="Dramatic Narrator",
                description="A dramatic narrator with expressive emotional range.",
                language="English",
            ),
            Voice(
                id="narrator_calm",
                name="Calm Narrator",
                description="A calm, soothing voice perfect for meditation or bedtime stories.",
                language="English",
            ),
            Voice(
                id="character_male_deep",
                name="Deep Male Voice",
                description="A deep, resonant male voice with gravitas.",
                language="English",
                gender="male",
            ),
            Voice(
                id="character_female_bright",
                name="Bright Female Voice",
                description="A bright, energetic female voice with enthusiasm.",
                language="English",
                gender="female",
            ),
        ]

        if language:
            return [v for v in voices if v.language is None or v.language == language]
        return voices

    def get_capabilities(self) -> List[TTSCapability]:
        """Get Qwen3-TTS capabilities."""
        return [
            TTSCapability.VOICE_CLONING,
            TTSCapability.VOICE_DESIGN,
            TTSCapability.MULTILINGUAL,
            TTSCapability.LOCAL,
            TTSCapability.LONG_FORM,
        ]

    def validate_config(self) -> Tuple[bool, Optional[str]]:
        """Validate configuration."""
        if self.config.model_variant:
            if self.config.model_variant not in QWEN_VARIANTS:
                return False, f"Unknown model variant: {self.config.model_variant}"
        return True, None

    def cleanup(self) -> None:
        """Unload model to free resources."""
        if self._model is not None:
            del self._model
            self._model = None
            self._model_name = None

            # Attempt to free GPU memory
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except:
                pass

        super().cleanup()

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return [
            "English",
            "Chinese",
            "Japanese",
            "Korean",
            "French",
            "German",
            "Spanish",
            "Italian",
            "Portuguese",
            "Russian",
            "Arabic",
        ]
