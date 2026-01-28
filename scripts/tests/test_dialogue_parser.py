#!/usr/bin/env python3
"""
Unit tests for dialogue_parser.py

Run with: python -m pytest scripts/tests/test_dialogue_parser.py -v
Or: python scripts/tests/test_dialogue_parser.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dialogue_parser import (
    Segment,
    detect_manuscript_format,
    extract_tagged_segments,
    extract_dialogue_segments,
    parse_manuscript,
    merge_adjacent_segments,
    normalize_speaker,
)


class TestFormatDetection:
    """Test format auto-detection."""

    def test_detects_tagged_format(self):
        text = """[NARRATOR]
The house was quiet.

[ELEANOR]
"Hello?"

[MARCUS]
"Over here."

[NARRATOR]
They met in the hallway.
"""
        assert detect_manuscript_format(text) == 'tagged'

    def test_detects_prose_format(self):
        text = """
The flower swayed in the breeze.

"Hello there," said Luna.

"Good morning," the flower replied.

Luna smiled and continued on her way.
"""
        assert detect_manuscript_format(text) == 'prose'

    def test_prose_with_few_brackets(self):
        # Only 1-2 bracketed items shouldn't trigger tagged detection
        text = """
Some text here.

[NARRATOR]
More text.

Some other prose content continues.
"""
        assert detect_manuscript_format(text) == 'prose'


class TestTaggedParser:
    """Test [SPEAKER] tag format parsing."""

    def test_basic_tagged_parsing(self):
        text = """[NARRATOR]
The room was dark.

[SARAH]
"Who's there?"

[NARRATOR]
A shadow moved.
"""
        segments = extract_tagged_segments(text)
        assert len(segments) == 3
        assert segments[0].speaker == 'narrator'
        assert segments[1].speaker == 'sarah'
        assert segments[1].is_dialogue is True
        assert segments[2].speaker == 'narrator'

    def test_multiword_speaker(self):
        text = """[PASTOR OAKES]
"Let us pray."

[NARRATOR]
The congregation bowed their heads.
"""
        segments = extract_tagged_segments(text)
        assert segments[0].speaker == 'pastor oakes'
        assert "pray" in segments[0].text

    def test_hyphenated_speaker(self):
        text = """[MARY-JANE]
"Hello there."
"""
        segments = extract_tagged_segments(text)
        assert segments[0].speaker == 'mary-jane'

    def test_empty_segments_filtered(self):
        text = """[NARRATOR]

[SARAH]
"Hello."

[NARRATOR]

[SARAH]
"Goodbye."
"""
        segments = extract_tagged_segments(text)
        # Empty narrator segments should be filtered
        assert all(s.text.strip() for s in segments)

    def test_preserves_multiline_content(self):
        text = """[NARRATOR]
The first paragraph.

The second paragraph.

The third paragraph.

[SARAH]
"Done."
"""
        segments = extract_tagged_segments(text)
        assert "first paragraph" in segments[0].text
        assert "second paragraph" in segments[0].text
        assert "third paragraph" in segments[0].text

    def test_sfx_tags_not_matched(self):
        """SFX/MUSIC cues should NOT be parsed as speakers."""
        text = """[NARRATOR]
The door creaked.

[SFX: door_creak]

[NARRATOR]
She entered.
"""
        segments = extract_tagged_segments(text)
        # SFX tag should be part of narration, not a speaker
        speakers = [s.speaker for s in segments]
        assert 'sfx' not in speakers
        assert 'sfx: door_creak' not in speakers


class TestProseParser:
    """Test prose dialogue attribution parsing."""

    def test_said_character_pattern(self):
        text = '"Hello," said Luna.'
        segments = extract_dialogue_segments(text)
        dialogue_segments = [s for s in segments if s.is_dialogue]
        assert len(dialogue_segments) >= 1
        assert any(s.speaker == 'luna' for s in dialogue_segments)

    def test_character_said_pattern(self):
        text = '"Hello," Luna said.'
        segments = extract_dialogue_segments(text)
        dialogue_segments = [s for s in segments if s.is_dialogue]
        assert len(dialogue_segments) >= 1

    def test_the_flower_alias(self):
        text = '"Hello," said the flower.'
        segments = extract_dialogue_segments(text)
        dialogue_segments = [s for s in segments if s.is_dialogue]
        assert any(s.speaker == 'flower' for s in dialogue_segments)


class TestMergeAdjacentSegments:
    """Test segment merging."""

    def test_merges_same_speaker(self):
        segments = [
            Segment("First.", "narrator", False, 0, 1),
            Segment("Second.", "narrator", False, 1, 2),
            Segment("Third.", "narrator", False, 2, 3),
        ]
        merged = merge_adjacent_segments(segments)
        assert len(merged) == 1
        assert "First" in merged[0].text
        assert "Third" in merged[0].text

    def test_no_merge_different_speakers(self):
        segments = [
            Segment("Hello.", "sarah", True, 0, 1),
            Segment("Hi.", "thomas", True, 1, 2),
        ]
        merged = merge_adjacent_segments(segments)
        assert len(merged) == 2

    def test_no_merge_different_dialogue_flag(self):
        segments = [
            Segment("She said.", "narrator", False, 0, 1),
            Segment("Hello.", "narrator", True, 1, 2),  # Different is_dialogue
        ]
        merged = merge_adjacent_segments(segments)
        assert len(merged) == 2


class TestNormalizeSpeaker:
    """Test speaker name normalization."""

    def test_lowercase(self):
        assert normalize_speaker("SARAH") == "sarah"

    def test_with_aliases(self):
        aliases = {"the bee": "bee", "flower": "flower"}
        assert normalize_speaker("the bee", aliases) == "bee"
        assert normalize_speaker("THE BEE", aliases) == "bee"

    def test_unknown_speaker(self):
        assert normalize_speaker("UNKNOWN") == "unknown"


class TestParseManuscript:
    """Test full parsing pipeline."""

    def test_auto_detects_format(self):
        tagged_text = """[NARRATOR]
Text.

[SARAH]
"Hello."

[NARRATOR]
More text.

[SARAH]
"Goodbye."
"""
        segments, stats = parse_manuscript(tagged_text)
        assert len(segments) >= 2
        assert 'narrator' in stats
        assert 'sarah' in stats

    def test_force_format(self):
        text = """[NARRATOR]
Text here.
"""
        # Force prose parsing (should find no dialogue)
        segments_prose, _ = parse_manuscript(text, force_format='prose')

        # Force tagged parsing
        segments_tagged, _ = parse_manuscript(text, force_format='tagged')

        # Tagged should find the NARRATOR segment
        assert any(s.speaker == 'narrator' for s in segments_tagged)

    def test_stats_accuracy(self):
        text = """[NARRATOR]
First narration.

[SARAH]
"Line one."

[SARAH]
"Line two."

[NARRATOR]
End.
"""
        segments, stats = parse_manuscript(text)

        assert stats['narrator']['segment_count'] == 2
        assert stats['sarah']['segment_count'] == 1  # Merged adjacent


class TestEdgeCases:
    """Test edge cases and potential failure modes."""

    def test_empty_text(self):
        segments, stats = parse_manuscript("")
        assert len(segments) == 0
        assert len(stats) == 0

    def test_only_whitespace(self):
        segments, stats = parse_manuscript("   \n\n\n   ")
        assert len(segments) == 0

    def test_unicode_content(self):
        text = """[NARRATOR]
The caf\u00e9 was quiet. She ordered an \u00e9clair.

[SARAH]
"\u00bfHola, c\u00f3mo est\u00e1s?"
"""
        segments, stats = parse_manuscript(text)
        assert len(segments) == 2
        assert "caf\u00e9" in segments[0].text
        assert "\u00bfHola" in segments[1].text

    def test_special_quotes(self):
        text = """[SARAH]
\u201cHello,\u201d she said. \u201cGoodbye.\u201d
"""
        segments, stats = parse_manuscript(text)
        assert len(segments) >= 1


def run_tests():
    """Run all tests without pytest."""
    import traceback

    test_classes = [
        TestFormatDetection,
        TestTaggedParser,
        TestProseParser,
        TestMergeAdjacentSegments,
        TestNormalizeSpeaker,
        TestParseManuscript,
        TestEdgeCases,
    ]

    passed = 0
    failed = 0
    errors = []

    for cls in test_classes:
        instance = cls()
        for name in dir(instance):
            if name.startswith('test_'):
                try:
                    getattr(instance, name)()
                    print(f"  \033[92m✓\033[0m {cls.__name__}.{name}")
                    passed += 1
                except AssertionError as e:
                    print(f"  \033[91m✗\033[0m {cls.__name__}.{name}: {e}")
                    failed += 1
                    errors.append((cls.__name__, name, traceback.format_exc()))
                except Exception as e:
                    print(f"  \033[91m✗\033[0m {cls.__name__}.{name}: {type(e).__name__}: {e}")
                    failed += 1
                    errors.append((cls.__name__, name, traceback.format_exc()))

    print(f"\n{passed} passed, {failed} failed")

    if errors and '-v' in sys.argv:
        print("\n--- Failures ---")
        for cls_name, test_name, tb in errors:
            print(f"\n{cls_name}.{test_name}:")
            print(tb)

    return failed == 0


if __name__ == "__main__":
    print("Running dialogue_parser tests...\n")
    success = run_tests()
    sys.exit(0 if success else 1)
