#!/usr/bin/env python3
"""
Unit tests for batch_produce.py configuration and report structures.

Tests cover dataclass validation, report serialization, and config defaults.
Does NOT require GPU or TTS engines — tests orchestration logic only.

Run with: python -m pytest scripts/tests/test_batch_produce.py -v
"""

import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from batch_produce import (
    ProductionConfig,
    ChapterStatus,
    ProductionReport,
)


# ---------------------------------------------------------------------------
# ProductionConfig
# ---------------------------------------------------------------------------

class TestProductionConfig:
    def test_required_fields(self):
        config = ProductionConfig(
            manuscript_path="book.txt",
            persona_path="voice.json",
        )
        assert config.manuscript_path == "book.txt"
        assert config.persona_path == "voice.json"

    def test_defaults(self):
        config = ProductionConfig(
            manuscript_path="book.txt",
            persona_path="voice.json",
        )
        assert config.output_dir == "audiobook_output"
        assert config.page_turns is False
        assert config.pause_duration == 2.0
        assert config.language == "English"
        assert config.no_tts is False
        assert config.no_postprocess is False
        assert config.no_validate is False
        assert config.keep_intermediate is False
        assert config.sample_duration_sec == 300.0

    def test_multispeaker_config(self):
        config = ProductionConfig(
            manuscript_path="book.txt",
            persona_path="voice.json",
            speaker_map_path="speakers.json",
        )
        assert config.speaker_map_path == "speakers.json"

    def test_metadata_fields(self):
        config = ProductionConfig(
            manuscript_path="book.txt",
            persona_path="voice.json",
            title="My Audiobook",
            author="Jane Doe",
            narrator="AI Voice",
            publisher="Self",
            copyright_year=2026,
            copyright_holder="Jane Doe",
        )
        assert config.title == "My Audiobook"
        assert config.copyright_year == 2026

    def test_content_type_options(self):
        for ct in [None, "auto", "childrens", "literary", "thriller", "nonfiction"]:
            config = ProductionConfig(
                manuscript_path="book.txt",
                persona_path="voice.json",
                content_type=ct,
            )
            assert config.content_type == ct


# ---------------------------------------------------------------------------
# ChapterStatus
# ---------------------------------------------------------------------------

class TestChapterStatus:
    def test_initial_state(self):
        status = ChapterStatus(
            number=1,
            title="Chapter One",
            text_file="ch01.txt",
        )
        assert status.tts_generated is False
        assert status.postprocessed is False
        assert status.acx_passed is None
        assert status.error is None
        assert status.acx_violations == []

    def test_tracks_progress(self):
        status = ChapterStatus(number=1, title="Ch1", text_file="ch01.txt")
        status.tts_generated = True
        status.raw_audio_file = "ch01_raw.wav"
        status.postprocessed = True
        status.final_audio_file = "ch01.mp3"
        status.acx_passed = True
        assert status.tts_generated is True
        assert status.acx_passed is True

    def test_error_state(self):
        status = ChapterStatus(number=1, title="Ch1", text_file="ch01.txt")
        status.error = "TTS generation failed: out of memory"
        assert "out of memory" in status.error

    def test_serializable(self):
        status = ChapterStatus(number=1, title="Ch1", text_file="ch01.txt")
        d = asdict(status)
        assert isinstance(d, dict)
        assert d["number"] == 1
        # Should be JSON serializable
        json_str = json.dumps(d)
        assert "Ch1" in json_str


# ---------------------------------------------------------------------------
# ProductionReport
# ---------------------------------------------------------------------------

class TestProductionReport:
    def test_empty_report(self):
        report = ProductionReport(
            title="Test",
            config={"manuscript": "book.txt"},
            started_at="2026-03-18T10:00:00",
        )
        assert report.title == "Test"
        assert len(report.chapters) == 0
        assert report.acx_passed == 0
        assert report.acx_failed == 0

    def test_to_dict(self):
        report = ProductionReport(
            title="Test",
            config={"manuscript": "book.txt"},
            started_at="2026-03-18T10:00:00",
        )
        d = report.to_dict()
        assert d["title"] == "Test"
        assert "started_at" in d
        assert "chapters" in d
        assert isinstance(d["chapters"], list)

    def test_to_dict_with_chapters(self):
        report = ProductionReport(
            title="Test",
            config={},
            started_at="2026-03-18T10:00:00",
        )
        report.chapters.append(
            ChapterStatus(number=1, title="Ch1", text_file="ch01.txt")
        )
        report.chapters.append(
            ChapterStatus(number=2, title="Ch2", text_file="ch02.txt")
        )
        d = report.to_dict()
        assert len(d["chapters"]) == 2
        assert d["chapters"][0]["number"] == 1

    def test_json_serializable(self):
        report = ProductionReport(
            title="Test",
            config={"key": "value"},
            started_at="2026-03-18T10:00:00",
            completed_at="2026-03-18T11:00:00",
            total_duration_sec=3600.0,
            total_word_count=50000,
            acx_passed=10,
            acx_failed=0,
        )
        report.chapters.append(
            ChapterStatus(number=1, title="Ch1", text_file="ch01.txt")
        )
        # Must not raise
        json_str = json.dumps(report.to_dict())
        assert "Test" in json_str

    def test_error_accumulation(self):
        report = ProductionReport(
            title="Test",
            config={},
            started_at="2026-03-18T10:00:00",
        )
        report.errors.append("Chapter 1 failed")
        report.errors.append("Chapter 5 failed")
        assert len(report.errors) == 2
        d = report.to_dict()
        assert len(d["errors"]) == 2

    def test_credits_tracking(self):
        report = ProductionReport(
            title="Test",
            config={},
            started_at="2026-03-18T10:00:00",
        )
        report.credits = {
            "opening_text": "prep/Opening_Credits.txt",
            "closing_text": "prep/Closing_Credits.txt",
        }
        d = report.to_dict()
        assert "opening_text" in d["credits"]
