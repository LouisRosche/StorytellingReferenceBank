"""
Kokoro TTS provider implementation.

Lightweight local TTS (82M params, 2-3 GB VRAM) for fast iteration:
persona auditions, voice prompt testing, golden reference drafts.

Not intended to replace Qwen3-TTS for final production — use it for
draft runs where speed matters more than maximum quality.

Install: pip install kokoro>=0.9.4 soundfile
System:  apt install espeak-ng  (Linux)

Documentation: https://huggingface.co/hexgrad/Kokoro-82M
"""

import sys
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from .base import (
    TTSProvider,
    TTSCapability,
    TTSResult,
    ProviderConfig,
    Voice,
)


# Language code mapping: full name → Kokoro code
LANG_CODES = {
    "english": "a",
    "american english": "a",
    "british english": "b",
    "spanish": "e",
    "french": "f",
    "hindi": "h",
    "italian": "i",
    "japanese": "j",
    "portuguese": "p",
    "brazilian portuguese": "p",
    "chinese": "z",
    "mandarin": "z",
    # Direct codes pass through
    "a": "a", "b": "b", "e": "e", "f": "f",
    "h": "h", "i": "i", "j": "j", "p": "p", "z": "z",
    # ISO codes
    "en": "a", "en-us": "a", "en-gb": "b",
    "es": "e", "fr": "f", "hi": "h",
    "it": "i", "ja": "j", "pt": "p", "zh": "z",
}

# Curated voice set for audiobook production.
# Naming convention: {lang}{gender}_{name}
# a=American, b=British; f=female, m=male
VOICES = {
    # American female
    "af_heart": Voice(
        id="af_heart", name="Heart", gender="female",
        language="en", description="Warm, expressive American female.",
    ),
    "af_bella": Voice(
        id="af_bella", name="Bella", gender="female",
        language="en", description="Clear, friendly American female.",
    ),
    "af_nicole": Voice(
        id="af_nicole", name="Nicole", gender="female",
        language="en", description="Smooth, professional American female.",
    ),
    "af_nova": Voice(
        id="af_nova", name="Nova", gender="female",
        language="en", description="Bright, engaging American female.",
    ),
    "af_sarah": Voice(
        id="af_sarah", name="Sarah", gender="female",
        language="en", description="Natural, conversational American female.",
    ),
    "af_sky": Voice(
        id="af_sky", name="Sky", gender="female",
        language="en", description="Light, youthful American female.",
    ),
    "af_river": Voice(
        id="af_river", name="River", gender="female",
        language="en", description="Calm, flowing American female.",
    ),
    # American male
    "am_adam": Voice(
        id="am_adam", name="Adam", gender="male",
        language="en", description="Deep, warm American male.",
    ),
    "am_michael": Voice(
        id="am_michael", name="Michael", gender="male",
        language="en", description="Clear, authoritative American male.",
    ),
    # British female
    "bf_emma": Voice(
        id="bf_emma", name="Emma", gender="female",
        language="en", description="Warm British female.",
    ),
    # British male
    "bm_george": Voice(
        id="bm_george", name="George", gender="male",
        language="en", description="Measured British male.",
    ),
    "bm_lewis": Voice(
        id="bm_lewis", name="Lewis", gender="male",
        language="en", description="Clear, narrative British male.",
    ),
}

# Default voice per language
DEFAULT_VOICE = {
    "a": "af_heart",
    "b": "bf_emma",
    "e": "ef_dora",
    "f": "ff_siwis",
    "h": "hf_alpha",
    "i": "if_sara",
    "j": "jf_alpha",
    "p": "pf_dora",
    "z": "zf_xiaobei",
}


class KokoroTTSProvider(TTSProvider):
    """
    Kokoro TTS provider — lightweight, fast, local.

    82M parameters, 2-3 GB VRAM, 96x real-time on consumer GPU.
    Ideal for fast persona iteration and draft production runs.

    Does NOT support voice cloning or voice design from natural language.
    Uses pre-trained voice embeddings selected by ID.

    Configuration:
        device: "cuda", "cpu" (default: auto-detect)
        default_language: Language code or name (default: "English")
        extra:
            voice: Default voice ID (default: "af_heart")
            speed: Default speed multiplier (default: 1.0)
    """

    def __init__(self, config: Optional[Union[ProviderConfig, Dict[str, Any]]] = None):
        super().__init__(config)
        self._pipelines = {}  # lang_code -> KPipeline

    @property
    def name(self) -> str:
        return "Kokoro"

    @property
    def provider_id(self) -> str:
        return "kokoro"

    def _resolve_lang_code(self, language: Optional[str] = None) -> str:
        """Resolve language name/code to Kokoro's single-char code."""
        if not language:
            language = self.config.default_language or "English"
        return LANG_CODES.get(language.lower(), "a")

    def _get_pipeline(self, lang_code: str):
        """Get or create a KPipeline for the given language code."""
        if lang_code in self._pipelines:
            return self._pipelines[lang_code]

        try:
            from kokoro import KPipeline
        except ImportError:
            raise ImportError(
                "Kokoro not installed. Install with: pip install kokoro>=0.9.4 soundfile\n"
                "Also requires espeak-ng: apt install espeak-ng (Linux)"
            )

        print(f"Loading Kokoro pipeline (lang={lang_code})...", file=sys.stderr)
        pipeline = KPipeline(lang_code=lang_code)
        self._pipelines[lang_code] = pipeline
        print("Kokoro ready.", file=sys.stderr)
        return pipeline

    def _do_initialize(self) -> None:
        """Pre-load the default language pipeline."""
        lang_code = self._resolve_lang_code()
        self._get_pipeline(lang_code)

    def generate(
        self,
        text: str,
        voice: Optional[Union[str, Voice]] = None,
        language: Optional[str] = None,
        output_path: Optional[str] = None,
        **kwargs
    ) -> TTSResult:
        """
        Generate speech using Kokoro.

        Args:
            text: Text to synthesize
            voice: Kokoro voice ID (e.g. "af_heart", "am_adam") or Voice object.
                   If a natural language description is passed, falls back to default.
            language: Language name or code
            output_path: Optional output file path
            **kwargs:
                speed: Speed multiplier (default: 1.0)
                split_pattern: Text splitting regex (default: r'\\n+')

        Returns:
            TTSResult with generated audio at 24000 Hz
        """
        self.initialize()

        lang_code = self._resolve_lang_code(language)
        pipeline = self._get_pipeline(lang_code)

        # Resolve voice
        if isinstance(voice, Voice):
            voice_id = voice.id
        elif voice and voice in VOICES:
            voice_id = voice
        elif voice and not voice.startswith(("a", "b", "e", "f", "h", "i", "j", "p", "z")):
            # Natural language description — can't use it, fall back to default
            voice_id = self.config.extra.get("voice", DEFAULT_VOICE.get(lang_code, "af_heart"))
        else:
            voice_id = voice or self.config.extra.get(
                "voice", DEFAULT_VOICE.get(lang_code, "af_heart")
            )

        speed = kwargs.get("speed", self.config.extra.get("speed", 1.0))
        split_pattern = kwargs.get("split_pattern", r'\n+')

        # Generate — Kokoro yields chunks, concatenate them
        chunks = []
        for gs, ps, audio in pipeline(text, voice=voice_id, speed=speed,
                                       split_pattern=split_pattern):
            if audio is not None:
                chunks.append(audio)

        if not chunks:
            raise RuntimeError("Kokoro generated no audio. Check text and voice ID.")

        audio = np.concatenate(chunks)
        sr = 24000
        duration = len(audio) / sr

        result = TTSResult(
            audio=audio,
            sample_rate=sr,
            duration_seconds=duration,
            metadata={
                "voice": voice_id,
                "language": lang_code,
                "speed": speed,
                "provider": "kokoro",
                "chunks": len(chunks),
            }
        )

        if output_path:
            self.save_audio(result, output_path)

        return result

    def list_voices(self, language: Optional[str] = None) -> List[Voice]:
        """
        List available Kokoro voices.

        Returns curated voices for audiobook production.
        For a full list, see: https://huggingface.co/hexgrad/Kokoro-82M
        """
        if language:
            lang_code = self._resolve_lang_code(language)
            prefix = lang_code
            return [v for v in VOICES.values()
                    if v.id.startswith(prefix) or v.id.startswith(lang_code)]
        return list(VOICES.values())

    def get_capabilities(self) -> List[TTSCapability]:
        """Get Kokoro capabilities."""
        return [
            TTSCapability.LOCAL,
            TTSCapability.MULTILINGUAL,
            TTSCapability.SPEED_CONTROL,
        ]

    def validate_config(self) -> Tuple[bool, Optional[str]]:
        """Validate configuration."""
        voice = self.config.extra.get("voice")
        if voice and not isinstance(voice, str):
            return False, f"voice must be a string, got {type(voice)}"
        return True, None

    def cleanup(self) -> None:
        """Unload pipelines to free resources."""
        self._pipelines.clear()

        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except (ImportError, Exception):
            pass

        super().cleanup()

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return [
            "English (American)",
            "English (British)",
            "Spanish",
            "French",
            "Hindi",
            "Italian",
            "Japanese",
            "Portuguese (Brazilian)",
            "Chinese (Mandarin)",
        ]
