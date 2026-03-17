"""
Coqui TTS / XTTS provider implementation.

Local TTS using Coqui's open-source models, including XTTS for voice cloning.

Models:
- XTTS v2: High-quality voice cloning, multilingual
- VITS: Fast, lightweight synthesis
- Various community models

Documentation: https://docs.coqui.ai/
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .base import (
    TTSProvider,
    TTSCapability,
    TTSResult,
    ProviderConfig,
    Voice,
)


class CoquiTTSProvider(TTSProvider):
    """
    Coqui TTS provider for local voice synthesis.

    STATUS: EXPERIMENTAL — generate(), generate_from_reference(), and
    list_voices() are not yet implemented and will raise NotImplementedError.
    Use Qwen or Kokoro providers for production workloads.

    Supports (when implemented):
    - Multiple TTS models (XTTS, VITS, Tacotron2, etc.)
    - Zero-shot voice cloning with XTTS
    - Fine-tuned custom voices
    - Multiple languages (varies by model)

    Configuration:
        model_name: Model to use (default: "tts_models/multilingual/multi-dataset/xtts_v2")
        model_path: Path to custom model (overrides model_name)
        device: Device to run on ("cuda", "cpu")
        use_gpu: Alias for device="cuda"

    Example:
        # Using XTTS v2 (default)
        provider = CoquiTTSProvider()

        # Using a specific model
        provider = CoquiTTSProvider({
            "extra": {
                "model_name": "tts_models/en/ljspeech/vits",
            }
        })

        # Using a custom model
        provider = CoquiTTSProvider({
            "model_path": "/path/to/my/model",
            "device": "cuda",
        })
    """

    # Popular pre-trained models
    MODELS = {
        # Multilingual models
        "xtts_v2": "tts_models/multilingual/multi-dataset/xtts_v2",
        "xtts_v1.1": "tts_models/multilingual/multi-dataset/xtts_v1.1",

        # English models
        "vits_ljspeech": "tts_models/en/ljspeech/vits",
        "vits_vctk": "tts_models/en/vctk/vits",
        "tacotron2_ljspeech": "tts_models/en/ljspeech/tacotron2-DDC",

        # Other languages
        "vits_de": "tts_models/de/thorsten/vits",
        "vits_es": "tts_models/es/css10/vits",
        "vits_fr": "tts_models/fr/css10/vits",
    }

    # Languages supported by XTTS v2
    XTTS_LANGUAGES = [
        "en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru",
        "nl", "cs", "ar", "zh-cn", "ja", "hu", "ko", "hi",
    ]

    def __init__(self, config: Optional[Union[ProviderConfig, Dict[str, Any]]] = None):
        super().__init__(config)
        self._tts = None
        self._model_name = None

    @property
    def name(self) -> str:
        return "Coqui TTS"

    @property
    def provider_id(self) -> str:
        return "coqui"

    def _get_device(self) -> str:
        """Determine device to use."""
        if self.config.device:
            return self.config.device

        if self.config.extra.get("use_gpu", True):
            try:
                import torch
                if torch.cuda.is_available():
                    return "cuda"
            except ImportError:
                pass

        return "cpu"

    def _do_initialize(self) -> None:
        """Load the TTS model."""
        self._load_model()

    def _load_model(self, model_name: Optional[str] = None):
        """
        Load or switch TTS model.

        Args:
            model_name: Model name or path. If None, uses config.
        """
        try:
            from TTS.api import TTS
        except ImportError:
            raise ImportError(
                "Coqui TTS not installed. Install with: pip install TTS"
            )

        # Determine model to load
        if model_name:
            target_model = model_name
        elif self.config.model_path:
            target_model = self.config.model_path
        else:
            model_key = self.config.extra.get("model_name", "xtts_v2")
            target_model = self.MODELS.get(model_key, model_key)

        # Skip if already loaded
        if self._tts is not None and self._model_name == target_model:
            return self._tts

        device = self._get_device()

        print(f"Loading Coqui TTS model: {target_model}...", file=__import__("sys").stderr)

        # Load model
        if os.path.isdir(target_model) or os.path.isfile(target_model):
            # Custom model path
            self._tts = TTS(model_path=target_model)
        else:
            # Named model from Coqui model hub
            self._tts = TTS(target_model)

        self._tts.to(device)
        self._model_name = target_model

        print(f"Model loaded on {device}", file=__import__("sys").stderr)
        return self._tts

    def _is_xtts(self) -> bool:
        """Check if current model is XTTS (supports cloning)."""
        return self._model_name and "xtts" in self._model_name.lower()

    def generate(
        self,
        text: str,
        voice: Optional[Union[str, Voice]] = None,
        language: Optional[str] = None,
        output_path: Optional[str] = None,
        **kwargs
    ) -> TTSResult:
        """
        Generate speech using Coqui TTS.

        For XTTS models, you can specify a reference audio for voice cloning.
        For other models, speaker can be specified if multi-speaker.

        Args:
            text: Text to synthesize
            voice: Speaker name (for multi-speaker models) or ignored
            language: Language code (e.g., "en", "es") - required for XTTS
            output_path: Optional output file path
            **kwargs:
                speaker: Speaker name for multi-speaker models
                speaker_wav: Path to reference audio (for XTTS cloning)

        Returns:
            TTSResult with generated audio
        """
        self.initialize()

        language = language or self.config.default_language or "en"

        # Map full language names to codes
        lang_map = {
            "english": "en", "spanish": "es", "french": "fr",
            "german": "de", "italian": "it", "portuguese": "pt",
            "chinese": "zh-cn", "japanese": "ja", "korean": "ko",
        }
        if language.lower() in lang_map:
            language = lang_map[language.lower()]

        # Get speaker/voice settings
        speaker = kwargs.get("speaker")
        if isinstance(voice, Voice):
            speaker = voice.id
        elif voice and not speaker:
            speaker = voice

        speaker_wav = kwargs.get("speaker_wav")

        # This would generate audio
        raise NotImplementedError(
            "Coqui TTS integration not yet implemented. "
            f"To implement: use self._tts.tts() with language={language}"
        )

        # Implementation would look like:
        # import numpy as np
        #
        # if self._is_xtts():
        #     if speaker_wav:
        #         # Voice cloning mode
        #         wav = self._tts.tts(
        #             text=text,
        #             speaker_wav=speaker_wav,
        #             language=language,
        #         )
        #     else:
        #         # Use default speaker or specify
        #         wav = self._tts.tts(
        #             text=text,
        #             language=language,
        #         )
        # else:
        #     # Non-XTTS model
        #     if speaker and hasattr(self._tts, 'speakers') and self._tts.speakers:
        #         wav = self._tts.tts(text=text, speaker=speaker)
        #     else:
        #         wav = self._tts.tts(text=text)
        #
        # audio = np.array(wav)
        # sr = self._tts.synthesizer.output_sample_rate
        # duration = len(audio) / sr
        #
        # result = TTSResult(
        #     audio=audio,
        #     sample_rate=sr,
        #     duration_seconds=duration,
        #     metadata={
        #         "model": self._model_name,
        #         "language": language,
        #         "speaker": speaker,
        #     }
        # )
        #
        # if output_path:
        #     self.save_audio(result, output_path)
        #
        # return result

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

        Requires XTTS model. reference_text is not required.

        Args:
            text: Text to synthesize
            reference_audio: Path to reference audio (3-15 seconds recommended)
            reference_text: Not required (ignored)
            output_path: Optional output file path
            **kwargs:
                language: Language code

        Returns:
            TTSResult with generated audio

        Raises:
            RuntimeError: If not using XTTS model
        """
        self.initialize()

        if not self._is_xtts():
            raise RuntimeError(
                f"Voice cloning requires XTTS model. Current model: {self._model_name}. "
                "Initialize with model_name='xtts_v2' for voice cloning support."
            )

        # Use the generate method with speaker_wav
        return self.generate(
            text=text,
            language=kwargs.get("language"),
            output_path=output_path,
            speaker_wav=reference_audio,
            **kwargs
        )

    def list_voices(self, language: Optional[str] = None) -> List[Voice]:
        """
        List available voices/speakers.

        For multi-speaker models, returns available speakers.
        For XTTS, returns guidance on voice cloning.

        Args:
            language: Filter by language (if applicable)

        Returns:
            List of available Voice objects
        """
        self.initialize()

        raise NotImplementedError(
            "Voice listing not yet implemented. "
            "To implement: check self._tts.speakers for multi-speaker models"
        )

        # Implementation would look like:
        # voices = []
        #
        # if self._is_xtts():
        #     # XTTS uses voice cloning, not preset voices
        #     voices.append(Voice(
        #         id="clone",
        #         name="Voice Clone",
        #         description="Clone any voice by providing reference audio. Use generate_from_reference().",
        #     ))
        # elif hasattr(self._tts, 'speakers') and self._tts.speakers:
        #     # Multi-speaker model
        #     for speaker in self._tts.speakers:
        #         voices.append(Voice(
        #             id=speaker,
        #             name=speaker,
        #             description=f"Pre-trained speaker: {speaker}",
        #         ))
        # else:
        #     # Single speaker model
        #     voices.append(Voice(
        #         id="default",
        #         name="Default",
        #         description="Single speaker model",
        #     ))
        #
        # return voices

    def get_capabilities(self) -> List[TTSCapability]:
        """Get Coqui TTS capabilities."""
        capabilities = [
            TTSCapability.LOCAL,
            TTSCapability.CUSTOM_MODELS,
        ]

        # XTTS-specific capabilities
        if self._initialized and self._is_xtts():
            capabilities.extend([
                TTSCapability.VOICE_CLONING,
                TTSCapability.MULTILINGUAL,
            ])

        return capabilities

    def validate_config(self) -> Tuple[bool, Optional[str]]:
        """Validate configuration."""
        # Check model path if specified
        if self.config.model_path:
            path = Path(self.config.model_path)
            if not path.exists():
                return False, f"Model path not found: {self.config.model_path}"

        # Check model name if specified
        model_name = self.config.extra.get("model_name")
        if model_name:
            # Allow both shorthand and full model names
            if model_name not in self.MODELS and not model_name.startswith("tts_models/"):
                return False, (
                    f"Unknown model: {model_name}. "
                    f"Available shortcuts: {list(self.MODELS.keys())}"
                )

        return True, None

    def cleanup(self) -> None:
        """Unload model to free resources."""
        if self._tts is not None:
            del self._tts
            self._tts = None
            self._model_name = None

            # Attempt to free GPU memory
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass

        super().cleanup()

    def list_available_models(self) -> Dict[str, str]:
        """
        List available models from Coqui model hub.

        Returns:
            Dict mapping model keys to full model names
        """
        raise NotImplementedError(
            "Model listing not yet implemented. "
            "To implement: use TTS.list_models() from the TTS API"
        )

        # Implementation would look like:
        # from TTS.api import TTS
        # return TTS().list_models()

    def get_supported_languages(self) -> List[str]:
        """
        Get languages supported by current model.

        Returns:
            List of language codes
        """
        if self._is_xtts():
            return self.XTTS_LANGUAGES

        # For other models, return based on model name
        if self._model_name:
            if "/en/" in self._model_name:
                return ["en"]
            elif "/de/" in self._model_name:
                return ["de"]
            elif "/es/" in self._model_name:
                return ["es"]
            elif "/fr/" in self._model_name:
                return ["fr"]

        return ["en"]  # Default fallback
