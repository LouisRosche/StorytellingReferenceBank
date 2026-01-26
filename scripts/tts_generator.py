#!/usr/bin/env python3
"""
Core Qwen3-TTS wrapper for audiobook production.

Supports:
- Loading voice personas from JSON
- Voice cloning (reference audio)
- Voice design (natural language prompts)
- Long-form content chunking
- ACX-compliant file naming

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
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional, Tuple, List, Generator
from dataclasses import dataclass

# Lazy imports for optional dependencies
_model = None
_model_name = None


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
        )


def get_model(model_variant: str = "1.7B-Base"):
    """
    Lazy-load the Qwen3-TTS model.

    Caches model instance to avoid reloading.
    """
    global _model, _model_name

    variant_map = {
        "1.7B-Base": "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
        "1.7B-VoiceDesign": "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
        "1.7B-CustomVoice": "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
        "0.6B": "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
    }

    model_name = variant_map.get(model_variant, variant_map["1.7B-Base"])

    if _model is not None and _model_name == model_name:
        return _model

    try:
        import torch
        from qwen_tts import Qwen3TTSModel
    except ImportError as e:
        print(f"Error: Missing dependency. Install with: pip install qwen-tts torch", file=sys.stderr)
        raise SystemExit(1) from e

    print(f"Loading model: {model_name}...", file=sys.stderr)

    # Determine device and dtype
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32

    # Try flash attention if available
    try:
        _model = Qwen3TTSModel.from_pretrained(
            model_name,
            device_map=device,
            dtype=dtype,
            attn_implementation="flash_attention_2"
        )
    except Exception:
        # Fall back without flash attention
        _model = Qwen3TTSModel.from_pretrained(
            model_name,
            device_map=device,
            dtype=dtype,
        )

    _model_name = model_name
    print(f"Model loaded on {device}", file=sys.stderr)
    return _model


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
) -> Tuple[list, int]:
    """
    Generate speech using voice cloning.

    Args:
        text: Text to synthesize
        ref_audio: Path to reference audio file (3-15 seconds optimal)
        ref_text: Transcript of reference audio
        language: Target language
        model_variant: Model to use

    Returns:
        Tuple of (waveform_array, sample_rate)
    """
    model = get_model(model_variant)

    wavs, sr = model.generate_voice_clone(
        text=text,
        language=language,
        ref_audio=ref_audio,
        ref_text=ref_text,
    )

    return wavs, sr


def generate_voice_design(
    text: str,
    voice_prompt: str,
    language: str = "English",
    model_variant: str = "1.7B-VoiceDesign",
) -> Tuple[list, int]:
    """
    Generate speech using natural language voice description.

    Args:
        text: Text to synthesize
        voice_prompt: Natural language description of desired voice
        language: Target language
        model_variant: Model to use (defaults to VoiceDesign variant)

    Returns:
        Tuple of (waveform_array, sample_rate)
    """
    model = get_model(model_variant)

    wavs, sr = model.generate_voice_design(
        text=text,
        language=language,
        instruct=voice_prompt,
    )

    return wavs, sr


def generate_from_persona(
    text: str,
    persona: Persona,
    language: str = "English",
) -> Tuple[list, int]:
    """
    Generate speech using a loaded persona.

    Automatically chooses voice cloning or voice design based on persona config.
    """
    # If persona has reference audio, use voice cloning
    if persona.reference_audio_path and persona.reference_audio_transcript:
        return generate_voice_clone(
            text=text,
            ref_audio=persona.reference_audio_path,
            ref_text=persona.reference_audio_transcript,
            language=language,
            model_variant=persona.model_variant,
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

    Yields:
        Tuple of (waveform_array, sample_rate) for each chunk
    """
    chunks = chunk_text(text, max_chunk_chars)
    total = len(chunks)

    for i, chunk in enumerate(chunks):
        if progress_callback:
            progress_callback(i + 1, total)

        if persona:
            wavs, sr = generate_from_persona(chunk, persona, language)
        elif ref_audio and ref_text:
            wavs, sr = generate_voice_clone(chunk, ref_audio, ref_text, language)
        elif voice_prompt:
            wavs, sr = generate_voice_design(chunk, voice_prompt, language)
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


def main():
    parser = argparse.ArgumentParser(
        description="Generate speech using Qwen3-TTS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--text", help="Text to synthesize")
    input_group.add_argument("--text-file", help="Path to text file")

    # Voice options
    voice_group = parser.add_argument_group("voice options")
    voice_group.add_argument("--persona", help="Path to persona JSON file")
    voice_group.add_argument("--voice-prompt", help="Natural language voice description")
    voice_group.add_argument("--ref-audio", help="Reference audio for voice cloning")
    voice_group.add_argument("--ref-text", help="Transcript of reference audio")

    # Output options
    parser.add_argument("--output", "-o", required=True, help="Output audio file path")
    parser.add_argument("--language", default="English", help="Target language (default: English)")
    parser.add_argument("--model", choices=["1.7B-Base", "1.7B-VoiceDesign", "1.7B-CustomVoice", "0.6B"],
                        help="Model variant (auto-selected based on voice options if not specified)")

    # Processing options
    parser.add_argument("--chunk-size", type=int, default=2000,
                        help="Max characters per chunk for long text (default: 2000)")
    parser.add_argument("--no-normalize", action="store_true",
                        help="Skip audio normalization")

    args = parser.parse_args()

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

    # Generate audio
    print(f"Generating speech for {len(text)} characters...", file=sys.stderr)

    def progress(current, total):
        print(f"Processing chunk {current}/{total}...", file=sys.stderr)

    chunks = list(generate_long_form(
        text=text,
        persona=persona,
        voice_prompt=args.voice_prompt,
        ref_audio=args.ref_audio,
        ref_text=args.ref_text,
        language=args.language,
        max_chunk_chars=args.chunk_size,
        progress_callback=progress if len(text) > args.chunk_size else None,
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
