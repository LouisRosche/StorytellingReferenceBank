#!/usr/bin/env python3
"""
Dialogue parser for multi-speaker TTS generation.

Parses text to identify speakers and splits content into segments
that can be rendered with different voice personas.

Supported patterns:
    - "Text," said Character.
    - "Text," Character said.
    - Character said, "Text."
    - "Text." (narrator continues)

Usage:
    python dialogue_parser.py manuscript.txt --speaker-map speakers.json
    python dialogue_parser.py manuscript.txt --output segments.json

Speaker map format:
    {
        "narrator": "personas/narrator.json",
        "Luna": "personas/luna-voice.json",
        "flower": "personas/flower-voice.json"
    }
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Dict, Tuple


@dataclass
class Segment:
    """A text segment with speaker attribution."""
    text: str
    speaker: str
    is_dialogue: bool
    line_start: int
    line_end: int

    def to_dict(self) -> dict:
        return asdict(self)


# Speech verbs for dialogue detection
SPEECH_VERBS = r'(?:said|asked|whispered|shouted|called|replied|answered|cried|laughed|murmured|exclaimed)'

# Character/speaker patterns (proper nouns and articles + nouns)
SPEAKER_PATTERN = r'(?:the\s+)?(?:[A-Z][a-z]+(?:\s+[a-z]+)*|[a-z]+\s+[a-z]+)'

# Dialogue attribution patterns
DIALOGUE_PATTERNS = [
    # "Text," said the flower. / "Text," said Luna. / "Text," laughed the storm clouds.
    (r'"([^"]+)"\s*,?\s*' + SPEECH_VERBS + r'\s+(' + SPEAKER_PATTERN + r')\.?', 'quote_verb_speaker'),
    # "Text," Luna said. / "Text," the flower said.
    (r'"([^"]+)"\s*,?\s*(' + SPEAKER_PATTERN + r')\s+' + SPEECH_VERBS + r'\.?', 'quote_speaker_verb'),
    # Luna said, "Text." / The flower said, "Text."
    (r'(' + SPEAKER_PATTERN + r')\s+' + SPEECH_VERBS + r'\s*,?\s*"([^"]+)"', 'speaker_verb_quote'),
]

# Pronoun to speaker context tracking
PRONOUNS = {'she', 'he', 'it', 'they'}

# Character aliases (normalize different references to same character)
DEFAULT_ALIASES = {
    "the flower": "flower",
    "the bee": "bee",
    "the storm clouds": "storm_clouds",
    "storm clouds": "storm_clouds",
    "big clouds": "storm_clouds",
    "the big clouds": "storm_clouds",
    "flower": "flower",
    "bee": "bee",
}


def normalize_speaker(speaker: str, aliases: Dict[str, str] = None) -> str:
    """Normalize speaker name to canonical form."""
    if aliases is None:
        aliases = DEFAULT_ALIASES

    lower = speaker.lower().strip()
    if lower in aliases:
        return aliases[lower]
    return lower


def extract_dialogue_segments(
    text: str,
    aliases: Dict[str, str] = None,
) -> List[Segment]:
    """
    Extract dialogue and narration segments from text.

    Returns list of Segments in document order.
    """
    if aliases is None:
        aliases = DEFAULT_ALIASES

    lines = text.split('\n')
    segments = []

    # Track position in text
    current_pos = 0

    # Track last named speaker for pronoun resolution
    last_named_speaker = None
    speaker_context = {}  # Maps pronouns to speakers based on context

    # Find all quoted sections and their speakers
    dialogue_matches = []

    for pattern, pattern_type in DIALOGUE_PATTERNS:
        for match in re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE):
            groups = match.groups()

            # Determine which group is dialogue and which is speaker based on pattern type
            if pattern_type == 'speaker_verb_quote':
                speaker = groups[0]
                dialogue_text = groups[1]
            else:
                dialogue_text = groups[0]
                speaker = groups[1]

            # Normalize speaker
            speaker_lower = speaker.lower().strip()

            # Handle pronoun speakers by looking at context
            if speaker_lower in PRONOUNS:
                # Pronouns need context-aware resolution
                # "she/he" typically refers to the protagonist in children's books
                # "it" refers to non-human speakers (flower, etc.)
                context_start = max(0, match.start() - 300)
                context = text[context_start:match.start()].lower()

                if speaker_lower == 'it':
                    # "it" typically refers to the most recent non-human speaker
                    for alias_key, alias_val in aliases.items():
                        if alias_key in context and alias_val not in ['luna']:
                            speaker = alias_val
                            break
                    else:
                        speaker = last_named_speaker or 'narrator'
                elif speaker_lower in ('she', 'he'):
                    # In children's books, "she/he" usually refers to protagonist
                    # Check if protagonist (Luna) was mentioned recently
                    if 'luna' in context:
                        speaker = 'luna'
                    elif last_named_speaker:
                        speaker = last_named_speaker
                    else:
                        speaker = 'narrator'
                else:
                    speaker = last_named_speaker or 'narrator'
            else:
                # Named speaker - normalize and track
                speaker = normalize_speaker(speaker, aliases)
                if speaker not in PRONOUNS:
                    last_named_speaker = speaker

            dialogue_matches.append({
                'start': match.start(),
                'end': match.end(),
                'text': dialogue_text,
                'speaker': speaker,
                'full_match': match.group(0),
            })

    # Also catch standalone quotes (speaker from context)
    # These are typically continuation quotes from the previous attributed speaker
    standalone_pattern = r'"([^"]+)"'
    for match in re.finditer(standalone_pattern, text):
        quote_text = match.group(1)
        # Check if this quote is already captured
        already_captured = any(
            m['start'] <= match.start() < m['end']
            for m in dialogue_matches
        )
        if not already_captured:
            # Standalone quote - inherit speaker from most recent attribution
            # Look backwards for the nearest speaker attribution
            nearest_speaker = None
            for dm in sorted(dialogue_matches, key=lambda x: x['start'], reverse=True):
                if dm['start'] < match.start():
                    nearest_speaker = dm['speaker']
                    break

            dialogue_matches.append({
                'start': match.start(),
                'end': match.end(),
                'text': quote_text,
                'speaker': nearest_speaker,  # Inherit from previous
                'full_match': match.group(0),
            })

    # Sort by position
    dialogue_matches.sort(key=lambda x: x['start'])

    # Calculate line numbers
    def pos_to_line(pos: int) -> int:
        return text[:pos].count('\n')

    # Build segment list, interleaving narration and dialogue
    current_pos = 0
    last_speaker = None

    for dm in dialogue_matches:
        # Narration before this dialogue
        if dm['start'] > current_pos:
            narration = text[current_pos:dm['start']].strip()
            if narration:
                segments.append(Segment(
                    text=narration,
                    speaker='narrator',
                    is_dialogue=False,
                    line_start=pos_to_line(current_pos),
                    line_end=pos_to_line(dm['start']),
                ))

        # The dialogue itself
        speaker = dm['speaker']
        if speaker is None:
            # Infer from context - check surrounding text for names
            context = text[max(0, dm['start']-100):dm['end']+100]
            for name in ['Luna', 'flower', 'bee', 'storm clouds']:
                if name.lower() in context.lower():
                    speaker = normalize_speaker(name, aliases)
                    break
            if speaker is None:
                speaker = last_speaker or 'narrator'

        segments.append(Segment(
            text=dm['text'],
            speaker=speaker,
            is_dialogue=True,
            line_start=pos_to_line(dm['start']),
            line_end=pos_to_line(dm['end']),
        ))

        last_speaker = speaker
        current_pos = dm['end']

    # Remaining narration
    if current_pos < len(text):
        remaining = text[current_pos:].strip()
        if remaining:
            segments.append(Segment(
                text=remaining,
                speaker='narrator',
                is_dialogue=False,
                line_start=pos_to_line(current_pos),
                line_end=len(lines),
            ))

    return segments


def merge_adjacent_segments(segments: List[Segment]) -> List[Segment]:
    """Merge adjacent segments with same speaker."""
    if not segments:
        return []

    merged = [segments[0]]

    for seg in segments[1:]:
        if seg.speaker == merged[-1].speaker and seg.is_dialogue == merged[-1].is_dialogue:
            # Merge
            merged[-1] = Segment(
                text=merged[-1].text + ' ' + seg.text,
                speaker=seg.speaker,
                is_dialogue=seg.is_dialogue,
                line_start=merged[-1].line_start,
                line_end=seg.line_end,
            )
        else:
            merged.append(seg)

    return merged


def analyze_speakers(segments: List[Segment]) -> Dict[str, dict]:
    """Analyze speaker statistics."""
    speakers = {}

    for seg in segments:
        if seg.speaker not in speakers:
            speakers[seg.speaker] = {
                'segment_count': 0,
                'word_count': 0,
                'dialogue_segments': 0,
                'narration_segments': 0,
            }

        speakers[seg.speaker]['segment_count'] += 1
        speakers[seg.speaker]['word_count'] += len(seg.text.split())

        if seg.is_dialogue:
            speakers[seg.speaker]['dialogue_segments'] += 1
        else:
            speakers[seg.speaker]['narration_segments'] += 1

    return speakers


def create_speaker_map_template(
    segments: List[Segment],
    output_path: str,
    default_persona_dir: str = "personas/",
) -> dict:
    """Create a template speaker map from detected speakers."""
    speakers = analyze_speakers(segments)

    speaker_map = {}
    for speaker in speakers:
        speaker_map[speaker] = {
            "persona_path": f"{default_persona_dir}{speaker}.json",
            "stats": speakers[speaker],
            "notes": f"Define persona for {speaker}",
        }

    return speaker_map


def parse_manuscript(
    text: str,
    speaker_map: Optional[Dict[str, str]] = None,
    merge_adjacent: bool = True,
    aliases: Dict[str, str] = None,
) -> Tuple[List[Segment], Dict[str, dict]]:
    """
    Full manuscript parsing pipeline.

    Args:
        text: Manuscript text
        speaker_map: Optional mapping of speaker -> persona path
        merge_adjacent: Merge adjacent segments with same speaker
        aliases: Character name aliases

    Returns:
        Tuple of (segments, speaker_stats)
    """
    segments = extract_dialogue_segments(text, aliases)

    if merge_adjacent:
        segments = merge_adjacent_segments(segments)

    stats = analyze_speakers(segments)

    return segments, stats


def format_for_tts(segments: List[Segment], speaker_map: Dict[str, str]) -> List[dict]:
    """
    Format segments for TTS generation pipeline.

    Returns list of dicts ready for batch_produce_multispeaker.py
    """
    tts_segments = []

    for i, seg in enumerate(segments):
        persona_path = speaker_map.get(seg.speaker, speaker_map.get('narrator'))

        tts_segments.append({
            'index': i,
            'text': seg.text,
            'speaker': seg.speaker,
            'persona_path': persona_path,
            'is_dialogue': seg.is_dialogue,
        })

    return tts_segments


def main():
    parser = argparse.ArgumentParser(
        description="Parse manuscript for multi-speaker TTS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("input", help="Manuscript file path")
    parser.add_argument("--speaker-map", help="JSON file mapping speakers to personas")
    parser.add_argument("--output", "-o", help="Output JSON file for segments")
    parser.add_argument("--create-map", action="store_true",
                        help="Create template speaker map from detected speakers")
    parser.add_argument("--no-merge", action="store_true",
                        help="Don't merge adjacent segments with same speaker")
    parser.add_argument("--stats", action="store_true",
                        help="Show speaker statistics")

    args = parser.parse_args()

    # Read input
    with open(args.input, 'r', encoding='utf-8') as f:
        text = f.read()

    # Load speaker map if provided
    speaker_map = None
    if args.speaker_map:
        with open(args.speaker_map, 'r') as f:
            speaker_map = json.load(f)

    # Parse
    segments, stats = parse_manuscript(
        text,
        speaker_map=speaker_map,
        merge_adjacent=not args.no_merge,
    )

    # Output
    if args.create_map:
        template = create_speaker_map_template(segments, args.output or "speaker_map.json")
        print(json.dumps(template, indent=2))

    elif args.stats:
        print(f"Found {len(segments)} segments")
        print(f"\nSpeakers:")
        for speaker, info in sorted(stats.items()):
            print(f"  {speaker}:")
            print(f"    Segments: {info['segment_count']}")
            print(f"    Words: {info['word_count']}")
            print(f"    Dialogue: {info['dialogue_segments']}")
            print(f"    Narration: {info['narration_segments']}")

    elif args.output:
        output_data = {
            'source_file': args.input,
            'segments': [s.to_dict() for s in segments],
            'speaker_stats': stats,
        }
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        print(f"Written: {args.output}", file=sys.stderr)

    else:
        # Print segments
        for i, seg in enumerate(segments):
            speaker_tag = f"[{seg.speaker}]" if seg.is_dialogue else f"({seg.speaker})"
            preview = seg.text[:60] + "..." if len(seg.text) > 60 else seg.text
            print(f"{i+1}. {speaker_tag} {preview}")


if __name__ == "__main__":
    main()
