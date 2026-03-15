#!/usr/bin/env python3
"""
Manuscript inspection and debugging tool.

Provides detailed analysis of a manuscript for TTS production:
- Segment breakdown with timing estimates
- Speaker distribution visualization
- Problem detection (long segments, missing speakers)
- Production metrics

Usage:
    python inspect_manuscript.py chapter.txt --speaker-map speakers.json
    python inspect_manuscript.py chapter.txt --stats
    python inspect_manuscript.py chapter.txt --problems
    python inspect_manuscript.py chapter.txt --export segments.json

Output modes:
    --stats: Summary statistics only
    --segments: List all segments with details
    --problems: Show only potential issues
    --export FILE: Export segments to JSON for external tools
"""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))

from dialogue_parser import parse_manuscript, Segment

# Optional readability analysis
try:
    import textstat
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False


def estimate_duration(text: str, wpm: int = 150) -> float:
    """Estimate speaking duration in seconds."""
    words = len(text.split())
    return (words / wpm) * 60


def analyze_segments(
    segments: List[Segment],
    speaker_map: Optional[Dict] = None
) -> Dict:
    """Analyze segments for production insights."""

    total_words = 0
    total_duration = 0.0
    speaker_stats = {}
    problems = []

    for i, seg in enumerate(segments):
        words = len(seg.text.split())
        duration = estimate_duration(seg.text)
        total_words += words
        total_duration += duration

        # Track speaker stats
        if seg.speaker not in speaker_stats:
            speaker_stats[seg.speaker] = {
                'segments': 0,
                'words': 0,
                'duration': 0.0,
                'dialogue_segments': 0,
                'narration_segments': 0,
                'longest_segment': 0,
            }

        speaker_stats[seg.speaker]['segments'] += 1
        speaker_stats[seg.speaker]['words'] += words
        speaker_stats[seg.speaker]['duration'] += duration
        speaker_stats[seg.speaker]['longest_segment'] = max(
            speaker_stats[seg.speaker]['longest_segment'],
            len(seg.text)
        )

        if seg.is_dialogue:
            speaker_stats[seg.speaker]['dialogue_segments'] += 1
        else:
            speaker_stats[seg.speaker]['narration_segments'] += 1

        # Detect problems
        if len(seg.text) > 2000:
            problems.append({
                'segment': i + 1,
                'speaker': seg.speaker,
                'issue': 'very_long',
                'detail': f'{len(seg.text)} chars - may hit token limits',
                'severity': 'warning'
            })

        if len(seg.text.strip()) < 5:
            problems.append({
                'segment': i + 1,
                'speaker': seg.speaker,
                'issue': 'very_short',
                'detail': f'Only {len(seg.text)} chars',
                'severity': 'warning'
            })

        # Check for unmapped speakers if speaker_map provided
        if speaker_map:
            speakers = speaker_map.get('speakers', {})
            aliases = speaker_map.get('aliases', {})
            all_valid = (
                set(k.lower() for k in speakers.keys()) |
                set(k.lower() for k in aliases.keys()) |
                {'narrator'}
            )
            if seg.speaker.lower() not in all_valid:
                problems.append({
                    'segment': i + 1,
                    'speaker': seg.speaker,
                    'issue': 'unmapped',
                    'detail': 'Not in speaker-map, will use default persona',
                    'severity': 'info'
                })

    result = {
        'summary': {
            'total_segments': len(segments),
            'total_words': total_words,
            'total_duration_seconds': round(total_duration, 1),
            'total_duration_formatted': format_duration(total_duration),
            'speakers': len(speaker_stats),
            'problems': len(problems),
        },
        'speakers': speaker_stats,
        'problems': problems,
    }

    # Add readability metrics when textstat is available
    if TEXTSTAT_AVAILABLE:
        full_text = " ".join(seg.text for seg in segments)
        result['readability'] = analyze_readability(full_text)

    return result


def analyze_readability(text: str) -> Dict:
    """
    Compute readability metrics using textstat.

    These metrics map directly to audience targeting:
    - Flesch Reading Ease > 80: children/easy (picture books)
    - Flesch Reading Ease 60-80: standard adult fiction
    - Flesch Reading Ease 30-60: advanced/literary
    - Flesch Reading Ease < 30: academic/technical

    The Flesch-Kincaid grade level maps to US school grade,
    which feeds persona_compatibility.py's audience matching.
    """
    return {
        'flesch_reading_ease': textstat.flesch_reading_ease(text),
        'flesch_kincaid_grade': textstat.flesch_kincaid_grade(text),
        'gunning_fog': textstat.gunning_fog(text),
        'automated_readability_index': textstat.automated_readability_index(text),
        'coleman_liau_index': textstat.coleman_liau_index(text),
        'dale_chall_score': textstat.dale_chall_readability_score(text),
        'difficult_words': textstat.difficult_words(text),
        'text_standard': textstat.text_standard(text, float_output=False),
        'reading_time_minutes': textstat.reading_time(text, ms_per_char=14.69) / 60000,
    }


def format_duration(seconds: float) -> str:
    """Format duration as MM:SS."""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}:{secs:02d}"


def print_stats(analysis: Dict):
    """Print summary statistics."""
    summary = analysis['summary']

    print("\n" + "=" * 50)
    print("MANUSCRIPT ANALYSIS")
    print("=" * 50)

    print(f"\nTotal segments: {summary['total_segments']}")
    print(f"Total words: {summary['total_words']}")
    print(f"Estimated duration: {summary['total_duration_formatted']} ({summary['total_duration_seconds']}s)")
    print(f"Unique speakers: {summary['speakers']}")

    print("\n" + "-" * 50)
    print("SPEAKER BREAKDOWN")
    print("-" * 50)

    # Sort speakers by word count
    sorted_speakers = sorted(
        analysis['speakers'].items(),
        key=lambda x: x[1]['words'],
        reverse=True
    )

    for speaker, stats in sorted_speakers:
        pct = (stats['words'] / summary['total_words']) * 100
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"\n  {speaker}")
        print(f"    {bar} {pct:.1f}%")
        print(f"    {stats['segments']} segments, {stats['words']} words, ~{format_duration(stats['duration'])}")
        print(f"    Dialogue: {stats['dialogue_segments']}, Narration: {stats['narration_segments']}")

    # Readability metrics (when textstat is available)
    if 'readability' in analysis:
        r = analysis['readability']
        print("\n" + "-" * 50)
        print("READABILITY")
        print("-" * 50)
        print(f"  Grade level: {r['text_standard']}")
        print(f"  Flesch Reading Ease: {r['flesch_reading_ease']:.1f}")
        print(f"  Flesch-Kincaid Grade: {r['flesch_kincaid_grade']:.1f}")
        print(f"  Gunning Fog Index: {r['gunning_fog']:.1f}")
        print(f"  Difficult words: {r['difficult_words']}")

        # Audience inference
        fre = r['flesch_reading_ease']
        if fre > 80:
            audience = "children / easy reading"
        elif fre > 60:
            audience = "standard adult fiction"
        elif fre > 30:
            audience = "advanced / literary"
        else:
            audience = "academic / technical"
        print(f"  Inferred audience: {audience}")


def print_segments(segments: List[Segment], analysis: Dict):
    """Print detailed segment list."""
    print("\n" + "=" * 50)
    print("SEGMENT DETAILS")
    print("=" * 50)

    for i, seg in enumerate(segments):
        duration = estimate_duration(seg.text)
        dtype = "D" if seg.is_dialogue else "N"
        preview = seg.text[:60].replace('\n', ' ')
        if len(seg.text) > 60:
            preview += "..."

        print(f"\n{i+1:3}. [{seg.speaker}] ({dtype}) ~{duration:.1f}s")
        print(f"     {preview}")


def print_problems(analysis: Dict):
    """Print detected problems."""
    problems = analysis['problems']

    print("\n" + "=" * 50)
    print("POTENTIAL ISSUES")
    print("=" * 50)

    if not problems:
        print("\n  ✓ No issues detected")
        return

    # Group by severity
    errors = [p for p in problems if p['severity'] == 'error']
    warnings = [p for p in problems if p['severity'] == 'warning']
    info = [p for p in problems if p['severity'] == 'info']

    for label, items, icon in [
        ("ERRORS", errors, "✗"),
        ("WARNINGS", warnings, "⚠"),
        ("INFO", info, "ℹ")
    ]:
        if items:
            print(f"\n{label}:")
            for p in items:
                print(f"  {icon} Segment {p['segment']} [{p['speaker']}]: {p['issue']}")
                print(f"      {p['detail']}")


def export_segments(segments: List[Segment], analysis: Dict, output_path: str):
    """Export segments to JSON."""
    data = {
        'analysis': analysis,
        'segments': [
            {
                'index': i + 1,
                'speaker': s.speaker,
                'is_dialogue': s.is_dialogue,
                'text': s.text,
                'word_count': len(s.text.split()),
                'char_count': len(s.text),
                'estimated_duration': estimate_duration(s.text),
                'line_start': s.line_start,
                'line_end': s.line_end,
            }
            for i, s in enumerate(segments)
        ]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Exported to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Inspect manuscript for TTS production",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument("manuscript", help="Manuscript file to inspect")
    parser.add_argument("--speaker-map", "-m", help="Speaker map JSON for validation")
    parser.add_argument("--stats", action="store_true", help="Show summary statistics")
    parser.add_argument("--segments", action="store_true", help="List all segments")
    parser.add_argument("--problems", action="store_true", help="Show only problems")
    parser.add_argument("--export", "-o", help="Export segments to JSON")
    parser.add_argument("--wpm", type=int, default=150, help="Words per minute for duration estimate")

    args = parser.parse_args()

    # Load manuscript
    with open(args.manuscript, 'r', encoding='utf-8') as f:
        text = f.read()

    # Load speaker map if provided
    speaker_map = None
    if args.speaker_map:
        with open(args.speaker_map, 'r') as f:
            speaker_map = json.load(f)

    # Parse
    segments, stats = parse_manuscript(text)

    # Analyze
    analysis = analyze_segments(segments, speaker_map)

    # Output
    if args.export:
        export_segments(segments, analysis, args.export)
    elif args.problems:
        print_problems(analysis)
    elif args.segments:
        print_segments(segments, analysis)
    else:
        # Default: show stats
        print_stats(analysis)
        if analysis['problems']:
            print_problems(analysis)


if __name__ == "__main__":
    main()
