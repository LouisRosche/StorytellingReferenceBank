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


from dialogue_parser import extract_sound_cues, strip_sound_cues, SoundCue


class TestExtractSoundCues:
    """Test extraction of sound design cues from manuscript text."""

    def test_extracts_sfx_cue(self):
        text = '[SFX: door_creak]'
        cues = extract_sound_cues(text)
        assert len(cues) == 1
        assert cues[0].cue_type == 'SFX'
        assert cues[0].content == 'door_creak'

    def test_extracts_music_cue(self):
        text = '[MUSIC: soft_piano]'
        cues = extract_sound_cues(text)
        assert len(cues) == 1
        assert cues[0].cue_type == 'MUSIC'
        assert cues[0].content == 'soft_piano'

    def test_extracts_ambiance_cue(self):
        text = '[AMBIANCE: forest_birds]'
        cues = extract_sound_cues(text)
        assert len(cues) == 1
        assert cues[0].cue_type == 'AMBIANCE'
        assert cues[0].content == 'forest_birds'

    def test_extracts_silence_cue(self):
        text = '[SILENCE: 2s]'
        cues = extract_sound_cues(text)
        assert len(cues) == 1
        assert cues[0].cue_type == 'SILENCE'
        assert cues[0].content == '2s'

    def test_extracts_multiple_cues_in_order(self):
        text = """[NARRATOR]
The door opened.

[SFX: door_creak]

[NARRATOR]
Wind howled outside.

[AMBIANCE: wind_howling]

[SILENCE: 1s]
"""
        cues = extract_sound_cues(text)
        assert len(cues) == 3
        assert cues[0].cue_type == 'SFX'
        assert cues[1].cue_type == 'AMBIANCE'
        assert cues[2].cue_type == 'SILENCE'
        # Positions should be in ascending order
        assert cues[0].position < cues[1].position < cues[2].position

    def test_no_cues_returns_empty(self):
        text = """[NARRATOR]
Just plain text with no sound cues.
"""
        cues = extract_sound_cues(text)
        assert len(cues) == 0

    def test_case_insensitive(self):
        text = '[sfx: footsteps]'
        cues = extract_sound_cues(text)
        assert len(cues) == 1
        assert cues[0].cue_type == 'SFX'

    def test_generation_hint_captured(self):
        text = '[SFX: door_creak] <!-- @generate: wooden door creaking slowly -->'
        cues = extract_sound_cues(text)
        assert len(cues) == 1
        assert cues[0].generation_hint == 'wooden door creaking slowly'

    def test_no_generation_hint_is_none(self):
        text = '[SFX: door_creak]'
        cues = extract_sound_cues(text)
        assert len(cues) == 1
        assert cues[0].generation_hint is None

    def test_generation_hint_with_music(self):
        text = (
            '[MUSIC: tension_build]'
            ' <!-- @generate: low rumbling tension building over 5 seconds -->'
        )
        cues = extract_sound_cues(text)
        assert len(cues) == 1
        assert cues[0].cue_type == 'MUSIC'
        assert cues[0].generation_hint is not None
        assert 'tension' in cues[0].generation_hint


class TestStripSoundCues:
    """Test removal of sound cues from text."""

    def test_strips_sfx_cue(self):
        text = 'Before.\n\n[SFX: door_creak]\n\nAfter.'
        cleaned = strip_sound_cues(text)
        assert '[SFX' not in cleaned
        assert 'Before.' in cleaned
        assert 'After.' in cleaned

    def test_strips_all_cue_types(self):
        text = """Text one.

[SFX: boom]

[MUSIC: piano]

[AMBIANCE: rain]

[SILENCE: 3s]

Text two."""
        cleaned = strip_sound_cues(text)
        assert '[SFX' not in cleaned
        assert '[MUSIC' not in cleaned
        assert '[AMBIANCE' not in cleaned
        assert '[SILENCE' not in cleaned
        assert 'Text one.' in cleaned
        assert 'Text two.' in cleaned

    def test_collapses_blank_lines(self):
        text = 'Line one.\n\n[SFX: boom]\n\n\n\nLine two.'
        cleaned = strip_sound_cues(text)
        # Should not have more than one blank line in a row
        assert '\n\n\n' not in cleaned

    def test_strips_generation_hints_too(self):
        text = 'Before.\n\n[SFX: creak] <!-- @generate: old wooden door -->\n\nAfter.'
        cleaned = strip_sound_cues(text)
        assert '@generate' not in cleaned
        assert '<!--' not in cleaned

    def test_empty_text(self):
        cleaned = strip_sound_cues('')
        assert cleaned == ''

    def test_text_without_cues_unchanged(self):
        text = 'Just regular text.\n\nNo cues here.'
        cleaned = strip_sound_cues(text)
        assert 'Just regular text.' in cleaned
        assert 'No cues here.' in cleaned


class TestSoundCueDataclass:
    """Test the SoundCue dataclass."""

    def test_fields(self):
        cue = SoundCue(cue_type='SFX', content='boom', position=0)
        assert cue.cue_type == 'SFX'
        assert cue.content == 'boom'
        assert cue.position == 0
        assert cue.generation_hint is None

    def test_generation_hint_field(self):
        cue = SoundCue(cue_type='MUSIC', content='piano', position=10,
                        generation_hint='gentle piano melody')
        assert cue.generation_hint == 'gentle piano melody'

    def test_to_dict(self):
        cue = SoundCue(cue_type='SFX', content='boom', position=42,
                        generation_hint='explosion sound')
        d = cue.to_dict()
        assert isinstance(d, dict)
        assert d['cue_type'] == 'SFX'
        assert d['content'] == 'boom'
        assert d['position'] == 42
        assert d['generation_hint'] == 'explosion sound'

    def test_to_dict_without_hint(self):
        cue = SoundCue(cue_type='SILENCE', content='2s', position=0)
        d = cue.to_dict()
        assert d['generation_hint'] is None


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
        TestExtractSoundCues,
        TestStripSoundCues,
        TestSoundCueDataclass,
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
