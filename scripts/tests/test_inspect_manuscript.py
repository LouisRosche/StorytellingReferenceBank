"""Tests for inspect_manuscript.py — manuscript analysis and problem detection."""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch
from dataclasses import dataclass

# Import Segment from dialogue_parser (conftest adds scripts/ to sys.path)
from dialogue_parser import Segment
from inspect_manuscript import (
    estimate_duration,
    analyze_segments,
    format_duration,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _seg(text, speaker="Narrator", is_dialogue=False, line_start=1, line_end=1):
    return Segment(
        text=text,
        speaker=speaker,
        is_dialogue=is_dialogue,
        line_start=line_start,
        line_end=line_end,
    )


# ---------------------------------------------------------------------------
# estimate_duration
# ---------------------------------------------------------------------------

class TestEstimateDuration:
    def test_basic(self):
        # 150 words at 150 wpm = 60 seconds
        text = " ".join(["word"] * 150)
        assert estimate_duration(text, wpm=150) == pytest.approx(60.0)

    def test_custom_wpm(self):
        text = " ".join(["word"] * 300)
        assert estimate_duration(text, wpm=300) == pytest.approx(60.0)

    def test_empty_text(self):
        assert estimate_duration("", wpm=150) == 0.0


# ---------------------------------------------------------------------------
# format_duration
# ---------------------------------------------------------------------------

class TestFormatDuration:
    def test_under_a_minute(self):
        assert format_duration(45.0) == "0:45"

    def test_exact_minutes(self):
        assert format_duration(120.0) == "2:00"

    def test_mixed(self):
        assert format_duration(90.0) == "1:30"


# ---------------------------------------------------------------------------
# analyze_segments — segment breakdown
# ---------------------------------------------------------------------------

class TestAnalyzeSegments:
    def test_summary_counts(self):
        segs = [
            _seg("Hello world"),
            _seg("How are you", speaker="Alice", is_dialogue=True),
        ]
        result = analyze_segments(segs)
        assert result["summary"]["total_segments"] == 2
        assert result["summary"]["speakers"] == 2

    def test_word_count(self):
        segs = [_seg("one two three")]
        result = analyze_segments(segs)
        assert result["summary"]["total_words"] == 3

    def test_speaker_stats_dialogue_narration(self):
        segs = [
            _seg("Narration text", speaker="Narrator", is_dialogue=False),
            _seg("Dialogue text", speaker="Narrator", is_dialogue=True),
        ]
        result = analyze_segments(segs)
        stats = result["speakers"]["Narrator"]
        assert stats["dialogue_segments"] == 1
        assert stats["narration_segments"] == 1
        assert stats["segments"] == 2


# ---------------------------------------------------------------------------
# analyze_segments — problem detection
# ---------------------------------------------------------------------------

class TestDetectProblems:
    def test_very_long_segment(self):
        long_text = "word " * 500  # >2000 chars
        segs = [_seg(long_text)]
        result = analyze_segments(segs)
        issues = [p for p in result["problems"] if p["issue"] == "very_long"]
        assert len(issues) == 1

    def test_very_short_segment(self):
        segs = [_seg("Hi")]
        result = analyze_segments(segs)
        issues = [p for p in result["problems"] if p["issue"] == "very_short"]
        assert len(issues) == 1

    def test_unmapped_speaker(self):
        speaker_map = {
            "speakers": {"alice": "persona.json"},
            "aliases": {},
        }
        segs = [_seg("Hello", speaker="Bob")]
        result = analyze_segments(segs, speaker_map=speaker_map)
        issues = [p for p in result["problems"] if p["issue"] == "unmapped"]
        assert len(issues) == 1
        assert issues[0]["speaker"] == "Bob"

    def test_mapped_speaker_no_problem(self):
        speaker_map = {
            "speakers": {"alice": "persona.json"},
            "aliases": {},
        }
        segs = [_seg("Hello", speaker="Alice")]
        result = analyze_segments(segs, speaker_map=speaker_map)
        unmapped = [p for p in result["problems"] if p["issue"] == "unmapped"]
        assert len(unmapped) == 0

    def test_narrator_always_valid(self):
        speaker_map = {
            "speakers": {},
            "aliases": {},
        }
        segs = [_seg("Once upon a time", speaker="narrator")]
        result = analyze_segments(segs, speaker_map=speaker_map)
        unmapped = [p for p in result["problems"] if p["issue"] == "unmapped"]
        assert len(unmapped) == 0

    def test_no_problems_clean(self):
        """A normal-length segment with no speaker map produces no problems."""
        segs = [_seg("A perfectly normal sentence of moderate length.")]
        result = analyze_segments(segs)
        assert result["summary"]["problems"] == 0
