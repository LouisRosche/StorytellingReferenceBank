"""Tests for inspect_manuscript.py — manuscript analysis, reporting, and CLI."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from dialogue_parser import Segment
from inspect_manuscript import (
    analyze_segments,
    estimate_duration,
    export_segments,
    format_duration,
    main,
    print_problems,
    print_segments,
    print_stats,
)

SAMPLE_MANUSCRIPT = Path(__file__).parent / "sample_childrens_story.txt"


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

    def test_zero(self):
        assert format_duration(0.0) == "0:00"


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

    def test_duration_estimate(self):
        segs = [_seg(" ".join(["word"] * 150))]
        result = analyze_segments(segs)
        assert result["summary"]["total_duration_seconds"] > 0

    def test_multiple_speakers(self):
        segs = [
            _seg("Line 1", speaker="Alice"),
            _seg("Line 2", speaker="Bob"),
            _seg("Line 3", speaker="Alice"),
        ]
        result = analyze_segments(segs)
        assert result["summary"]["speakers"] == 2
        assert "Alice" in result["speakers"]
        assert "Bob" in result["speakers"]
        assert result["speakers"]["Alice"]["segments"] == 2


# ---------------------------------------------------------------------------
# analyze_segments — problem detection
# ---------------------------------------------------------------------------


class TestDetectProblems:
    def test_very_long_segment(self):
        long_text = "word " * 500
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
        segs = [_seg("A perfectly normal sentence of moderate length.")]
        result = analyze_segments(segs)
        assert result["summary"]["problems"] == 0


# ---------------------------------------------------------------------------
# print_stats
# ---------------------------------------------------------------------------


class TestPrintStats:
    def test_prints_summary(self, capsys):
        segs = [
            _seg("Once upon a time there was a cat."),
            _seg("Hello!", speaker="Alice", is_dialogue=True),
        ]
        analysis = analyze_segments(segs)
        print_stats(analysis)
        captured = capsys.readouterr()
        assert "MANUSCRIPT ANALYSIS" in captured.out
        assert "SPEAKER BREAKDOWN" in captured.out
        assert "Narrator" in captured.out
        assert "Alice" in captured.out


# ---------------------------------------------------------------------------
# print_segments
# ---------------------------------------------------------------------------


class TestPrintSegments:
    def test_prints_segment_details(self, capsys):
        segs = [
            _seg("Narration here.", speaker="Narrator"),
            _seg("Dialogue here.", speaker="Alice", is_dialogue=True),
        ]
        analysis = analyze_segments(segs)
        print_segments(segs, analysis)
        captured = capsys.readouterr()
        assert "SEGMENT DETAILS" in captured.out
        assert "[Narrator]" in captured.out
        assert "[Alice]" in captured.out
        assert "(N)" in captured.out  # Narration
        assert "(D)" in captured.out  # Dialogue

    def test_truncates_long_text(self, capsys):
        long_text = "a" * 100
        segs = [_seg(long_text)]
        analysis = analyze_segments(segs)
        print_segments(segs, analysis)
        captured = capsys.readouterr()
        assert "..." in captured.out


# ---------------------------------------------------------------------------
# print_problems
# ---------------------------------------------------------------------------


class TestPrintProblems:
    def test_no_problems(self, capsys):
        analysis = {"problems": []}
        print_problems(analysis)
        captured = capsys.readouterr()
        assert "No issues detected" in captured.out

    def test_shows_problems(self, capsys):
        analysis = {
            "problems": [
                {
                    "segment": 1,
                    "speaker": "Bob",
                    "issue": "unmapped",
                    "detail": "Speaker not in map",
                    "severity": "warning",
                },
                {
                    "segment": 2,
                    "speaker": "Narrator",
                    "issue": "very_long",
                    "detail": "Segment too long",
                    "severity": "error",
                },
            ]
        }
        print_problems(analysis)
        captured = capsys.readouterr()
        assert "ERRORS" in captured.out
        assert "WARNINGS" in captured.out
        assert "very_long" in captured.out
        assert "unmapped" in captured.out


# ---------------------------------------------------------------------------
# export_segments
# ---------------------------------------------------------------------------


class TestExportSegments:
    def test_exports_json(self, tmp_path, capsys):
        segs = [
            _seg("Hello world", speaker="Narrator"),
            _seg("Hi there", speaker="Alice", is_dialogue=True),
        ]
        analysis = analyze_segments(segs)
        output = str(tmp_path / "export.json")
        export_segments(segs, analysis, output)

        data = json.loads(Path(output).read_text())
        assert "analysis" in data
        assert "segments" in data
        assert len(data["segments"]) == 2
        assert data["segments"][0]["speaker"] == "Narrator"
        assert data["segments"][1]["is_dialogue"] is True

        captured = capsys.readouterr()
        assert "Exported" in captured.out


# ---------------------------------------------------------------------------
# main() — CLI
# ---------------------------------------------------------------------------


class TestMain:
    def test_default_shows_stats(self, capsys):
        with patch("sys.argv", ["inspect_manuscript.py", str(SAMPLE_MANUSCRIPT)]):
            main()
        captured = capsys.readouterr()
        assert "MANUSCRIPT ANALYSIS" in captured.out

    def test_problems_flag(self, capsys):
        with patch("sys.argv", ["inspect_manuscript.py", str(SAMPLE_MANUSCRIPT), "--problems"]):
            main()
        captured = capsys.readouterr()
        assert "POTENTIAL ISSUES" in captured.out

    def test_segments_flag(self, capsys):
        with patch("sys.argv", ["inspect_manuscript.py", str(SAMPLE_MANUSCRIPT), "--segments"]):
            main()
        captured = capsys.readouterr()
        assert "SEGMENT DETAILS" in captured.out

    def test_export_flag(self, tmp_path, capsys):
        output = str(tmp_path / "out.json")
        argv = ["inspect_manuscript.py", str(SAMPLE_MANUSCRIPT), "--export", output]
        with patch("sys.argv", argv):
            main()
        assert Path(output).exists()
        data = json.loads(Path(output).read_text())
        assert "segments" in data

    def test_with_speaker_map(self, tmp_path, capsys):
        speaker_map = tmp_path / "speakers.json"
        speaker_map.write_text(
            json.dumps(
                {
                    "speakers": {"Narrator": "persona.json"},
                    "aliases": {},
                }
            )
        )
        with patch(
            "sys.argv",
            [
                "inspect_manuscript.py",
                str(SAMPLE_MANUSCRIPT),
                "--speaker-map",
                str(speaker_map),
            ],
        ):
            main()
        captured = capsys.readouterr()
        assert "MANUSCRIPT ANALYSIS" in captured.out
