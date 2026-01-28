#!/usr/bin/env python3
"""
Multi-speaker TTS generator for audiobook production.

Generates audio with different voices for narrator and dialogue characters.
Uses dialogue_parser.py to segment text, then renders each segment with
the appropriate voice persona.

Usage:
    # Full production with speaker map
    python multispeaker_tts.py manuscript.txt --speaker-map speakers.json --output output.wav

    # Dry run to see segments
    python multispeaker_tts.py manuscript.txt --speaker-map speakers.json --dry-run

    # With custom crossfade
    python multispeaker_tts.py manuscript.txt --speaker-map speakers.json \
        --crossfade 150 --output output.wav
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Tuple

# Add script directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from dialogue_parser import parse_manuscript, Segment


@dataclass
class SpeakerMap:
    """Configuration for multi-speaker production."""
    title: str
    default_persona: str
    speakers: Dict[str, dict]
    aliases: Dict[str, str]
    crossfade_ms: int = 100
    dialogue_pause_ms: int = 200
    page_turn_pause_ms: int = 2500

    @classmethod
    def from_json(cls, path: str, base_dir: str = None) -> "SpeakerMap":
        """Load speaker map from JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Resolve relative paths
        if base_dir is None:
            base_dir = str(Path(path).parent)

        default_persona = data.get('default_persona', '')
        if default_persona and not os.path.isabs(default_persona):
            default_persona = os.path.join(base_dir, default_persona)

        speakers = {}
        for speaker, info in data.get('speakers', {}).items():
            persona_path = info.get('persona_path', '')
            if persona_path and not os.path.isabs(persona_path):
                persona_path = os.path.join(base_dir, persona_path)
            speakers[speaker] = {**info, 'persona_path': persona_path}

        production = data.get('production_notes', {})

        return cls(
            title=data.get('title', 'Untitled'),
            default_persona=default_persona,
            speakers=speakers,
            aliases=data.get('aliases', {}),
            crossfade_ms=production.get('crossfade_ms', 100),
            dialogue_pause_ms=production.get('dialogue_pause_ms', 200),
            page_turn_pause_ms=production.get('page_turn_pause_ms', 2500),
        )

    def get_persona_path(self, speaker: str) -> str:
        """Get persona path for a speaker (case-insensitive lookup)."""
        # Direct lookup first
        if speaker in self.speakers:
            return self.speakers[speaker].get('persona_path', self.default_persona)

        # Case-insensitive lookup
        speaker_lower = speaker.lower()
        for key, info in self.speakers.items():
            if key.lower() == speaker_lower:
                return info.get('persona_path', self.default_persona)

        # Check aliases (also case-insensitive)
        for alias, canonical in self.aliases.items():
            if alias.lower() == speaker_lower:
                return self.get_persona_path(canonical)

        return self.default_persona


def generate_multispeaker_audio(
    segments: List[Segment],
    speaker_map: SpeakerMap,
    language: str = "English",
    verbose: bool = False,
    progress_callback: Optional[callable] = None,
) -> Tuple[list, int]:
    """
    Generate audio for multiple speakers.

    Args:
        segments: List of text segments with speaker attribution
        speaker_map: Speaker-to-persona mapping
        language: Target language
        verbose: Print progress
        progress_callback: Optional callback(segment_num, total)

    Returns:
        Tuple of (combined_waveform, sample_rate)
    """
    from tts_generator import Persona, generate_from_persona

    try:
        import numpy as np
    except ImportError:
        print("Error: numpy required. Install with: pip install numpy", file=sys.stderr)
        sys.exit(1)

    # Cache loaded personas
    persona_cache = {}

    def get_persona(speaker: str) -> Persona:
        persona_path = speaker_map.get_persona_path(speaker)
        if persona_path not in persona_cache:
            if verbose:
                print(f"  Loading persona: {persona_path}", file=sys.stderr)
            persona_cache[persona_path] = Persona.from_json(persona_path)
        return persona_cache[persona_path]

    # Generate audio for each segment
    audio_segments = []
    sample_rate = None

    total = len(segments)
    for i, seg in enumerate(segments):
        if progress_callback:
            progress_callback(i + 1, total)

        if verbose:
            speaker_tag = f"[{seg.speaker}]" if seg.is_dialogue else f"({seg.speaker})"
            preview = seg.text[:40] + "..." if len(seg.text) > 40 else seg.text
            print(f"  {i+1}/{total} {speaker_tag} {preview}", file=sys.stderr)

        try:
            persona = get_persona(seg.speaker)
            wavs, sr = generate_from_persona(seg.text, persona, language)

            # Extract audio array
            audio = wavs[0] if isinstance(wavs, list) else wavs
            if hasattr(audio, 'cpu'):
                audio = audio.cpu().numpy()

            audio_segments.append({
                'audio': audio,
                'speaker': seg.speaker,
                'is_dialogue': seg.is_dialogue,
            })

            if sample_rate is None:
                sample_rate = sr

        except Exception as e:
            print(f"  ERROR generating segment {i+1}: {e}", file=sys.stderr)
            # Insert silence placeholder
            if sample_rate:
                silence_duration = max(1, len(seg.text.split()) * 0.3)  # ~0.3s per word
                silence = np.zeros(int(sample_rate * silence_duration))
                audio_segments.append({
                    'audio': silence,
                    'speaker': seg.speaker,
                    'is_dialogue': seg.is_dialogue,
                    'error': str(e),
                })

    if not audio_segments or sample_rate is None:
        raise ValueError("No audio generated")

    # Concatenate with appropriate transitions
    combined = []
    crossfade_samples = int(sample_rate * speaker_map.crossfade_ms / 1000)
    dialogue_pause_samples = int(sample_rate * speaker_map.dialogue_pause_ms / 1000)

    for i, seg in enumerate(audio_segments):
        audio = seg['audio']

        # Add pause before dialogue (if switching from narration)
        if i > 0 and seg['is_dialogue'] and not audio_segments[i-1]['is_dialogue']:
            combined.append(np.zeros(dialogue_pause_samples))

        # Add crossfade with previous segment if speakers differ
        if i > 0 and seg['speaker'] != audio_segments[i-1]['speaker']:
            if len(combined) > 0 and crossfade_samples > 0:
                # Simple crossfade: fade out previous, fade in current
                overlap = min(crossfade_samples, len(audio), len(combined[-1]) if combined else 0)
                if overlap > 0:
                    fade_out = np.linspace(1, 0, overlap)
                    fade_in = np.linspace(0, 1, overlap)

                    # Apply to end of previous
                    if combined:
                        combined[-1][-overlap:] *= fade_out

                    # Apply to start of current
                    audio = audio.copy()
                    audio[:overlap] *= fade_in

        combined.append(audio)

        # Add pause after dialogue (if switching to narration)
        if i < len(audio_segments) - 1:
            next_seg = audio_segments[i + 1]
            if seg['is_dialogue'] and not next_seg['is_dialogue']:
                combined.append(np.zeros(dialogue_pause_samples))

    # Concatenate all
    final_audio = np.concatenate(combined)

    return [final_audio], sample_rate


def process_manuscript_multispeaker(
    input_path: str,
    speaker_map_path: str,
    output_path: str,
    language: str = "English",
    dry_run: bool = False,
    verbose: bool = False,
) -> dict:
    """
    Full multi-speaker processing pipeline.

    Args:
        input_path: Path to manuscript file
        speaker_map_path: Path to speaker map JSON
        output_path: Output audio file path
        language: Target language
        dry_run: Only show segments, don't generate
        verbose: Print progress

    Returns:
        Dict with processing stats
    """
    from tts_generator import save_audio

    # Load input
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Load speaker map
    speaker_map = SpeakerMap.from_json(speaker_map_path)

    if verbose:
        print(f"Loaded speaker map: {speaker_map.title}", file=sys.stderr)
        print(f"Speakers: {list(speaker_map.speakers.keys())}", file=sys.stderr)

    # Parse manuscript
    segments, stats = parse_manuscript(text, aliases=speaker_map.aliases)

    if verbose:
        print(f"\nParsed {len(segments)} segments:", file=sys.stderr)
        for speaker, info in stats.items():
            print(f"  {speaker}: {info['segment_count']} segments, {info['word_count']} words", file=sys.stderr)

    if dry_run:
        print("\n[DRY RUN] Segments:", file=sys.stderr)
        for i, seg in enumerate(segments):
            persona_path = speaker_map.get_persona_path(seg.speaker)
            speaker_tag = f"[{seg.speaker}]" if seg.is_dialogue else f"({seg.speaker})"
            preview = seg.text[:50] + "..." if len(seg.text) > 50 else seg.text
            print(f"  {i+1}. {speaker_tag} → {Path(persona_path).stem}", file=sys.stderr)
            print(f"      {preview}", file=sys.stderr)
        return {'segments': len(segments), 'dry_run': True}

    # Generate audio
    if verbose:
        print(f"\nGenerating audio...", file=sys.stderr)

    def progress(current, total):
        if verbose:
            pass  # Already printing in generate function

    wavs, sr = generate_multispeaker_audio(
        segments,
        speaker_map,
        language=language,
        verbose=verbose,
        progress_callback=progress,
    )

    # Save
    save_audio(wavs, sr, output_path, normalize=True)

    if verbose:
        print(f"\nSaved: {output_path}", file=sys.stderr)

    return {
        'segments': len(segments),
        'speakers': list(stats.keys()),
        'output': output_path,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate multi-speaker TTS audio",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("input", help="Manuscript file path")
    parser.add_argument("--speaker-map", required=True,
                        help="Speaker map JSON file")
    parser.add_argument("--output", "-o", help="Output audio file path")
    parser.add_argument("--language", default="English",
                        help="Target language (default: English)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show segments without generating audio")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose output")

    args = parser.parse_args()

    # Validate
    if not os.path.exists(args.input):
        print(f"Error: Input not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(args.speaker_map):
        print(f"Error: Speaker map not found: {args.speaker_map}", file=sys.stderr)
        sys.exit(1)

    if not args.dry_run and not args.output:
        parser.error("--output required unless using --dry-run")

    try:
        result = process_manuscript_multispeaker(
            input_path=args.input,
            speaker_map_path=args.speaker_map,
            output_path=args.output,
            language=args.language,
            dry_run=args.dry_run,
            verbose=args.verbose,
        )

        if not args.dry_run:
            print(f"Generated {result['segments']} segments with {len(result['speakers'])} speakers")
            print(f"Output: {result['output']}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
