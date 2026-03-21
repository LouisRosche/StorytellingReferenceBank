#!/usr/bin/env python3
"""
Core TTS wrapper for audiobook production.

Supports:
- Loading voice personas from JSON
- Voice cloning (reference audio)
- Voice design (natural language prompts)
- Long-form content chunking
- ACX-compliant file naming
- Multiple TTS providers (Qwen, ElevenLabs, OpenAI, Coqui)

Usage:
    # Voice design from persona
    python tts_generator.py --persona personas/examples/narrator-literary.json \
        --text "Your text here" --output output.wav

    # Voice cloning with reference audio
    python tts_generator.py --ref-audio reference.wav --ref-text "Transcript" \
        --text "Your text here" --output output.wav

    # From text file
    python tts_generator.py --persona personas/examples/narrator-childrens.json \
        --text-file chapter.txt --output Chapter_01.wav

    # Use a different provider
    python tts_generator.py --provider elevenlabs --text "Hello" --output out.wav
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional, Tuple, List, Generator, Union
from dataclasses import dataclass

# Lazy imports for provider system and optional dependencies
_provider_instance = None
_provider_id = None
_provider_config = None


@dataclass
class Persona:
    """Voice persona loaded from JSON."""
    id: str
    name: str
    voice_prompt: str
    character_context: Optional[str] = None
    reference_audio_path: Optional[str] = None
    reference_audio_transcript: Optional[str] = None
    model_variant: str = "1.7B-Base"
    provider: Optional[str] = None  # Allow persona to specify provider

    @classmethod
    def from_json(cls, path: str) -> "Persona":
        """Load persona from JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        ref_audio = data.get("reference_audio", {})
        return cls(
            id=data["id"],
            name=data["name"],
            voice_prompt=data["voice_prompt"],
            character_context=data.get("character_context"),
            reference_audio_path=ref_audio.get("path"),
            reference_audio_transcript=ref_audio.get("transcript"),
            model_variant=data.get("model_variant", "1.7B-Base"),
            provider=data.get("provider"),
        )


def get_provider(
    provider_id: Optional[str] = None,
    config: Optional[dict] = None,
    model_variant: Optional[str] = None,
):
    """
    Get or create a TTS provider instance.

    Caches provider instance to avoid reloading models.

    Args:
        provider_id: Provider to use ("qwen", "elevenlabs", "openai", "coqui")
        config: Provider configuration dict
        model_variant: Model variant for Qwen (legacy compatibility)

    Returns:
        TTSProvider instance
    """
    global _provider_instance, _provider_id, _provider_config

    # Default to qwen provider
    target_id = provider_id or "qwen"

    # Build config
    target_config = config or {}
    if model_variant and target_id == "qwen":
        target_config["model_variant"] = model_variant

    # Check if we can reuse cached provider
    if (
        _provider_instance is not None
        and _provider_id == target_id
        and _provider_config == target_config
    ):
        return _provider_instance

    # Import providers (lazy import to avoid loading until needed)
    try:
        from tts_providers import get_provider as _get_provider
    except ImportError:
        # Fallback for when providers module not available
        raise ImportError(
            "TTS providers module not found. Ensure tts_providers/ is in the scripts directory."
        )

    # Create new provider
    _provider_instance = _get_provider(target_id, target_config)
    _provider_id = target_id
    _provider_config = target_config

    return _provider_instance


def get_model(model_variant: str = "1.7B-Base"):
    """
    Legacy function: Get the Qwen3-TTS model.

    This function is maintained for backward compatibility.
    New code should use get_provider() instead.

    Args:
        model_variant: Model variant to load

    Returns:
        The underlying model (for Qwen provider)
    """
    provider = get_provider(provider_id="qwen", model_variant=model_variant)
    provider.initialize()

    # Return the internal model for backward compatibility
    return provider._model


def chunk_text(text: str, max_chars: int = 2000) -> List[str]:
    """
    Split text into chunks for long-form generation.

    Splits on sentence boundaries to preserve natural flow.
    Default max_chars tuned for ~30-60 seconds of speech per chunk.
    """
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


def generate_voice_clone(
    text: str,
    ref_audio: str,
    ref_text: str,
    language: str = "English",
    model_variant: str = "1.7B-Base",
    provider_id: Optional[str] = None,
) -> Tuple[list, int]:
    """
    Generate speech using voice cloning.

    Args:
        text: Text to synthesize
        ref_audio: Path to reference audio file (3-15 seconds optimal)
        ref_text: Transcript of reference audio
        language: Target language
        model_variant: Model to use (for Qwen provider)
        provider_id: TTS provider to use (default: "qwen")

    Returns:
        Tuple of (waveform_array, sample_rate)
    """
    provider = get_provider(
        provider_id=provider_id,
        model_variant=model_variant if provider_id in (None, "qwen") else None,
    )

    result = provider.generate_from_reference(
        text=text,
        reference_audio=ref_audio,
        reference_text=ref_text,
        language=language,
        model_variant=model_variant,
    )

    return result.to_tuple()


def generate_voice_design(
    text: str,
    voice_prompt: str,
    language: str = "English",
    model_variant: str = "1.7B-VoiceDesign",
    provider_id: Optional[str] = None,
) -> Tuple[list, int]:
    """
    Generate speech using natural language voice description.

    Args:
        text: Text to synthesize
        voice_prompt: Natural language description of desired voice
        language: Target language
        model_variant: Model to use (for Qwen provider, defaults to VoiceDesign variant)
        provider_id: TTS provider to use (default: "qwen")

    Returns:
        Tuple of (waveform_array, sample_rate)
    """
    provider = get_provider(
        provider_id=provider_id,
        model_variant=model_variant if provider_id in (None, "qwen") else None,
    )

    result = provider.generate(
        text=text,
        voice=voice_prompt,
        language=language,
        model_variant=model_variant,
    )

    return result.to_tuple()


def generate_from_persona(
    text: str,
    persona: Persona,
    language: str = "English",
    provider_id: Optional[str] = None,
) -> Tuple[list, int]:
    """
    Generate speech using a loaded persona.

    Automatically chooses voice cloning or voice design based on persona config.

    Args:
        text: Text to synthesize
        persona: Loaded Persona object
        language: Target language
        provider_id: TTS provider to use (default: persona.provider or "qwen")

    Returns:
        Tuple of (waveform_array, sample_rate)
    """
    # Use persona-specified provider if available
    target_provider = provider_id or persona.provider

    # If persona has reference audio, use voice cloning
    if persona.reference_audio_path and persona.reference_audio_transcript:
        return generate_voice_clone(
            text=text,
            ref_audio=persona.reference_audio_path,
            ref_text=persona.reference_audio_transcript,
            language=language,
            model_variant=persona.model_variant,
            provider_id=target_provider,
        )

    # Otherwise use voice design with the prompt
    # Use VoiceDesign variant for natural language prompts
    model_variant = persona.model_variant
    if model_variant == "1.7B-Base":
        model_variant = "1.7B-VoiceDesign"

    return generate_voice_design(
        text=text,
        voice_prompt=persona.voice_prompt,
        language=language,
        model_variant=model_variant,
        provider_id=target_provider,
    )


def generate_long_form(
    text: str,
    persona: Optional[Persona] = None,
    voice_prompt: Optional[str] = None,
    ref_audio: Optional[str] = None,
    ref_text: Optional[str] = None,
    language: str = "English",
    max_chunk_chars: int = 2000,
    progress_callback: Optional[callable] = None,
    provider_id: Optional[str] = None,
) -> Generator[Tuple[list, int], None, None]:
    """
    Generate speech for long-form content with chunking.

    Yields (waveform, sample_rate) tuples for each chunk.
    Use this for streaming-like processing of long texts.

    Args:
        text: Full text to synthesize
        persona: Voice persona (if provided, overrides other voice params)
        voice_prompt: Natural language voice description
        ref_audio: Reference audio for cloning
        ref_text: Transcript of reference audio
        language: Target language
        max_chunk_chars: Maximum characters per chunk
        progress_callback: Optional callback(chunk_num, total_chunks)
        provider_id: TTS provider to use (default: "qwen")

    Yields:
        Tuple of (waveform_array, sample_rate) for each chunk
    """
    chunks = chunk_text(text, max_chunk_chars)
    total = len(chunks)

    for i, chunk in enumerate(chunks):
        if progress_callback:
            progress_callback(i + 1, total)

        if persona:
            wavs, sr = generate_from_persona(chunk, persona, language, provider_id)
        elif ref_audio and ref_text:
            wavs, sr = generate_voice_clone(chunk, ref_audio, ref_text, language, provider_id=provider_id)
        elif voice_prompt:
            wavs, sr = generate_voice_design(chunk, voice_prompt, language, provider_id=provider_id)
        else:
            raise ValueError("Must provide persona, voice_prompt, or ref_audio+ref_text")

        yield wavs, sr


def save_audio(
    waveform,
    sample_rate: int,
    output_path: str,
    normalize: bool = True,
):
    """
    Save waveform to audio file.

    Args:
        waveform: Audio waveform array
        sample_rate: Sample rate in Hz
        output_path: Output file path (supports .wav, .mp3, .flac)
        normalize: Normalize audio levels
    """
    try:
        import soundfile as sf
        import numpy as np
    except ImportError as e:
        print("Error: Missing dependency. Install with: pip install soundfile numpy", file=sys.stderr)
        raise SystemExit(1) from e

    # Handle list output from model
    audio = waveform[0] if isinstance(waveform, list) else waveform

    # Convert to numpy if needed
    if hasattr(audio, 'cpu'):
        audio = audio.cpu().numpy()

    # Normalize if requested
    if normalize:
        max_val = np.abs(audio).max()
        if max_val > 0:
            audio = audio / max_val * 0.95  # Leave headroom

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    sf.write(output_path, audio, sample_rate)
    print(f"Saved: {output_path}", file=sys.stderr)


def concatenate_audio(audio_chunks: List[Tuple[list, int]], gap_seconds: float = 0.5) -> Tuple[list, int]:
    """
    Concatenate multiple audio chunks with optional gaps.

    Args:
        audio_chunks: List of (waveform, sample_rate) tuples
        gap_seconds: Silence gap between chunks

    Returns:
        Combined (waveform, sample_rate) tuple
    """
    try:
        import numpy as np
    except ImportError as e:
        print("Error: Missing dependency. Install with: pip install numpy", file=sys.stderr)
        raise SystemExit(1) from e

    if not audio_chunks:
        raise ValueError("No audio chunks to concatenate")

    # Use first chunk's sample rate as reference
    _, sr = audio_chunks[0]
    gap_samples = int(sr * gap_seconds)
    gap = np.zeros(gap_samples)

    combined = []
    for i, (wav, chunk_sr) in enumerate(audio_chunks):
        audio = wav[0] if isinstance(wav, list) else wav
        if hasattr(audio, 'cpu'):
            audio = audio.cpu().numpy()

        combined.append(audio)
        if i < len(audio_chunks) - 1:  # Add gap except after last chunk
            combined.append(gap)

    return [np.concatenate(combined)], sr


def acx_filename(title: str, chapter_num: Optional[int] = None, chapter_name: Optional[str] = None) -> str:
    """
    Generate ACX-compliant filename.

    Format: Title_Chapter_01.wav or Title_Opening_Credits.wav
    """
    # Clean title for filename
    clean_title = re.sub(r'[^\w\s-]', '', title).strip()
    clean_title = re.sub(r'\s+', '_', clean_title)

    if chapter_num is not None:
        return f"{clean_title}_Chapter_{chapter_num:02d}.wav"
    elif chapter_name:
        clean_name = re.sub(r'[^\w\s-]', '', chapter_name).strip()
        clean_name = re.sub(r'\s+', '_', clean_name)
        return f"{clean_title}_{clean_name}.wav"
    else:
        return f"{clean_title}.wav"


def list_available_providers():
    """List available TTS providers."""
    try:
        from tts_providers import list_providers
        return list_providers()
    except ImportError:
        return {"qwen": "Qwen3-TTS (default)"}


def main():
    parser = argparse.ArgumentParser(
        description="Generate speech using TTS providers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--text", help="Text to synthesize")
    input_group.add_argument("--text-file", help="Path to text file")
    input_group.add_argument("--list-providers", action="store_true",
                             help="List available TTS providers and exit")

    # Voice options
    voice_group = parser.add_argument_group("voice options")
    voice_group.add_argument("--persona", help="Path to persona JSON file")
    voice_group.add_argument("--voice-prompt", help="Natural language voice description")
    voice_group.add_argument("--ref-audio", help="Reference audio for voice cloning")
    voice_group.add_argument("--ref-text", help="Transcript of reference audio")

    # Provider options
    provider_group = parser.add_argument_group("provider options")
    provider_group.add_argument("--provider", default="qwen",
                                help="TTS provider to use (default: qwen)")
    # API keys should be set via environment variables (e.g. ELEVENLABS_API_KEY),
    # not passed on the command line where they appear in process listings and shell history.

    # Output options
    parser.add_argument("--output", "-o", help="Output audio file path")
    parser.add_argument("--language", default="English", help="Target language (default: English)")
    parser.add_argument("--model", choices=["1.7B-Base", "1.7B-VoiceDesign", "1.7B-CustomVoice", "0.6B"],
                        help="Model variant for Qwen provider (auto-selected based on voice options if not specified)")

    # Processing options
    parser.add_argument("--chunk-size", type=int, default=2000,
                        help="Max characters per chunk for long text (default: 2000)")
    parser.add_argument("--no-normalize", action="store_true",
                        help="Skip audio normalization")

    args = parser.parse_args()

    # Handle --list-providers
    if args.list_providers:
        print("Available TTS Providers:")
        print("-" * 40)
        for provider_id, name in list_available_providers().items():
            default = " (default)" if provider_id == "qwen" else ""
            print(f"  {provider_id}: {name}{default}")
        print("\nUse --provider <id> to select a provider.")
        return

    # Require --output for actual generation
    if not args.output:
        parser.error("--output is required for speech generation")

    # Load text
    if args.text:
        text = args.text
    else:
        with open(args.text_file, "r", encoding="utf-8") as f:
            text = f.read()

    # Validate voice options
    persona = None
    if args.persona:
        persona = Persona.from_json(args.persona)
    elif not args.voice_prompt and not (args.ref_audio and args.ref_text):
        parser.error("Must provide --persona, --voice-prompt, or --ref-audio with --ref-text")

    if args.ref_audio and not args.ref_text:
        parser.error("--ref-audio requires --ref-text")

    # Build provider config
    provider_config = {}
    if args.model and args.provider == "qwen":
        provider_config["model_variant"] = args.model

    # Generate audio
    print(f"Generating speech for {len(text)} characters using {args.provider}...", file=sys.stderr)

    def progress(current, total):
        print(f"Processing chunk {current}/{total}...", file=sys.stderr)

    # Pre-initialize provider if config provided
    if provider_config:
        get_provider(provider_id=args.provider, config=provider_config)

    chunks = list(generate_long_form(
        text=text,
        persona=persona,
        voice_prompt=args.voice_prompt,
        ref_audio=args.ref_audio,
        ref_text=args.ref_text,
        language=args.language,
        max_chunk_chars=args.chunk_size,
        progress_callback=progress if len(text) > args.chunk_size else None,
        provider_id=args.provider,
    ))

    # Concatenate if multiple chunks
    if len(chunks) > 1:
        wavs, sr = concatenate_audio(chunks)
    else:
        wavs, sr = chunks[0]

    # Save
    save_audio(wavs, sr, args.output, normalize=not args.no_normalize)
    print("Done!", file=sys.stderr)


if __name__ == "__main__":
    main()
