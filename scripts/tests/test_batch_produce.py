#!/usr/bin/env python3
"""
Unit tests for batch_produce.py — config, report, and pipeline stage logic.

Tests cover dataclass validation, report serialization, config defaults,
and pipeline stages with mocked TTS/audio processing.
Does NOT require GPU or TTS engines — tests orchestration logic only.

Run with: python -m pytest scripts/tests/test_batch_produce.py -v
"""

import json
import os
import shutil
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from batch_produce import (
    ProductionConfig,
    ChapterStatus,
    ProductionReport,
    stage_prep,
    stage_tts,
    stage_master,
    stage_validate,
    stage_sample,
    stage_cleanup,
    run_pipeline,
    print_summary,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_MANUSCRIPT = Path(__file__).parent / "sample_childrens_story.txt"


@pytest.fixture
def tmp_output(tmp_path):
    return str(tmp_path / "output")


@pytest.fixture
def basic_config(tmp_path, tmp_output):
    """Config pointing at the sample manuscript with TTS/postprocess/validate skipped."""
    persona = tmp_path / "persona.json"
    persona.write_text(json.dumps({
        "id": "test-narrator",
        "name": "Test Narrator",
        "voice_prompt": "A warm voice",
    }))
    return ProductionConfig(
        manuscript_path=str(SAMPLE_MANUSCRIPT),
        persona_path=str(persona),
        output_dir=tmp_output,
        no_tts=True,
        no_postprocess=True,
        no_validate=True,
        title="Test Book",
        author="Test Author",
        narrator="Test Narrator",
    )


@pytest.fixture
def basic_report():
    return ProductionReport(
        title="Test",
        config={"manuscript": "book.txt"},
        started_at="2026-03-18T10:00:00",
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

    def test_save_creates_file(self, tmp_path):
        report = ProductionReport(
            title="Test Save",
            config={"k": "v"},
            started_at="2026-03-18T10:00:00",
        )
        out = str(tmp_path / "report.json")
        report.save(out)
        assert os.path.exists(out)
        loaded = json.loads(Path(out).read_text())
        assert loaded["title"] == "Test Save"


# ---------------------------------------------------------------------------
# stage_prep — splits manuscript, extracts cues, generates credits
# ---------------------------------------------------------------------------

class TestStagePrep:
    def test_splits_manuscript_into_chapters(self, basic_config, basic_report):
        stage_prep(basic_config, basic_report)
        assert len(basic_report.chapters) >= 1
        assert basic_report.total_word_count > 0

    def test_creates_prep_directory(self, basic_config, basic_report):
        stage_prep(basic_config, basic_report)
        prep_dir = Path(basic_config.output_dir) / "prep"
        assert prep_dir.exists()

    def test_generates_credits_when_author_set(self, basic_config, basic_report):
        stage_prep(basic_config, basic_report)
        assert "opening_text" in basic_report.credits
        assert "closing_text" in basic_report.credits
        assert os.path.exists(basic_report.credits["opening_text"])
        assert os.path.exists(basic_report.credits["closing_text"])

    def test_no_credits_without_author(self, basic_config, basic_report):
        basic_config.author = None
        basic_config.narrator = None
        stage_prep(basic_config, basic_report)
        assert basic_report.credits == {}

    def test_chapter_text_files_exist(self, basic_config, basic_report):
        stage_prep(basic_config, basic_report)
        for ch in basic_report.chapters:
            assert os.path.exists(ch.text_file)

    def test_detects_content_type(self, basic_config, basic_report):
        stage_prep(basic_config, basic_report)
        assert "content_type" in basic_report.config

    def test_explicit_content_type_used(self, basic_config, basic_report):
        basic_config.content_type = "thriller"
        stage_prep(basic_config, basic_report)
        assert basic_report.config["content_type"] == "thriller"

    def test_verbose_output(self, basic_config, basic_report, capsys):
        stage_prep(basic_config, basic_report, verbose=True)
        captured = capsys.readouterr()
        assert "STAGE 1" in captured.out
        assert "Split into" in captured.out


# ---------------------------------------------------------------------------
# stage_tts — routes to single/multi speaker, or skips on --no-tts
# ---------------------------------------------------------------------------

class TestStageTts:
    def test_skips_when_no_tts(self, basic_config, basic_report):
        basic_config.no_tts = True
        result = stage_tts(basic_config, basic_report)
        assert result == Path(basic_config.output_dir) / "raw_audio"

    def test_skips_verbose_message(self, basic_config, basic_report, capsys):
        basic_config.no_tts = True
        stage_tts(basic_config, basic_report, verbose=True)
        captured = capsys.readouterr()
        assert "SKIPPED" in captured.out

    def test_creates_raw_dir_for_single_speaker(self, basic_config, basic_report, tmp_path):
        basic_config.no_tts = False
        # Set up a chapter with text
        ch_file = tmp_path / "ch01.txt"
        ch_file.write_text("Hello world")
        basic_report.chapters.append(
            ChapterStatus(number=1, title="Ch1", text_file=str(ch_file))
        )

        mock_persona = MagicMock()
        mock_persona.name = "Test"

        import numpy as np
        fake_audio = np.zeros(1000)

        with patch("batch_produce.stage_tts.__module__", "batch_produce"):
            with patch("tts_generator.Persona") as MockPersona, \
                 patch("tts_generator.generate_from_persona") as mock_gen, \
                 patch("tts_generator.save_audio") as mock_save:
                MockPersona.from_json.return_value = mock_persona
                mock_gen.return_value = ([fake_audio], 44100)

                stage_tts(basic_config, basic_report)

                mock_gen.assert_called_once()
                mock_save.assert_called()
                assert basic_report.chapters[0].tts_generated

    def test_routes_to_multispeaker(self, basic_config, basic_report, tmp_path):
        basic_config.no_tts = False
        basic_config.speaker_map_path = str(tmp_path / "speakers.json")

        ch_file = tmp_path / "ch01.txt"
        ch_file.write_text('"Hello," said Alice.')
        basic_report.chapters.append(
            ChapterStatus(number=1, title="Ch1", text_file=str(ch_file))
        )

        # Write speaker map
        (tmp_path / "speakers.json").write_text(json.dumps({
            "default_persona": "persona.json",
            "speakers": {},
            "aliases": {},
        }))

        import numpy as np
        fake_audio = np.zeros(1000)

        mock_persona = MagicMock()
        mock_persona.name = "Test"

        with patch("tts_generator.Persona") as MockPersona, \
             patch("tts_generator.save_audio"), \
             patch("multispeaker_tts.generate_multispeaker_audio") as mock_multi:
            MockPersona.from_json.return_value = mock_persona
            mock_multi.return_value = ([fake_audio], 44100)

            stage_tts(basic_config, basic_report)


# ---------------------------------------------------------------------------
# stage_master — post-processing
# ---------------------------------------------------------------------------

class TestStageMaster:
    def test_skips_when_no_postprocess(self, basic_config, basic_report, capsys):
        basic_config.no_postprocess = True
        result = stage_master(basic_config, basic_report, verbose=True)
        captured = capsys.readouterr()
        assert "SKIPPED" in captured.out

    def test_copies_raw_to_final_when_skipped(self, basic_config, basic_report, tmp_path):
        basic_config.no_postprocess = True
        raw_file = tmp_path / "raw.wav"
        raw_file.write_bytes(b"fake audio")
        basic_report.chapters.append(
            ChapterStatus(number=1, title="Ch1", text_file="ch01.txt",
                          raw_audio_file=str(raw_file))
        )
        stage_master(basic_config, basic_report)
        assert basic_report.chapters[0].final_audio_file == str(raw_file)


# ---------------------------------------------------------------------------
# stage_validate — ACX validation
# ---------------------------------------------------------------------------

class TestStageValidate:
    def test_skips_when_no_validate(self, basic_config, basic_report, capsys):
        basic_config.no_validate = True
        stage_validate(basic_config, basic_report, verbose=True)
        captured = capsys.readouterr()
        assert "SKIPPED" in captured.out

    def test_skips_chapters_without_final_audio(self, basic_config, basic_report):
        basic_config.no_validate = False
        basic_report.chapters.append(
            ChapterStatus(number=1, title="Ch1", text_file="ch01.txt")
        )
        # Should not raise — just skips
        stage_validate(basic_config, basic_report)
        assert basic_report.acx_passed == 0
        assert basic_report.acx_failed == 0

    def test_records_validation_pass(self, basic_config, basic_report, tmp_path):
        basic_config.no_validate = False
        audio_file = tmp_path / "ch01.mp3"
        audio_file.write_bytes(b"fake")

        basic_report.chapters.append(
            ChapterStatus(number=1, title="Ch1", text_file="ch01.txt",
                          final_audio_file=str(audio_file))
        )

        mock_validation = MagicMock()
        mock_validation.passed = True
        mock_validation.checks = []

        with patch("acx_validator.validate_audio", return_value=mock_validation):
            stage_validate(basic_config, basic_report)
            assert basic_report.acx_passed == 1
            assert basic_report.acx_failed == 0

    def test_records_validation_failure(self, basic_config, basic_report, tmp_path):
        basic_config.no_validate = False
        audio_file = tmp_path / "ch01.mp3"
        audio_file.write_bytes(b"fake")

        basic_report.chapters.append(
            ChapterStatus(number=1, title="Ch1", text_file="ch01.txt",
                          final_audio_file=str(audio_file))
        )

        mock_check = MagicMock()
        mock_check.name = "loudness"
        mock_check.message = "too loud"
        mock_check.severity.value = "fail"

        mock_validation = MagicMock()
        mock_validation.passed = False
        mock_validation.checks = [mock_check]

        with patch("acx_validator.validate_audio", return_value=mock_validation):
            stage_validate(basic_config, basic_report)
            assert basic_report.acx_failed == 1
            assert len(basic_report.chapters[0].acx_violations) == 1

    def test_handles_validation_exception(self, basic_config, basic_report, tmp_path):
        basic_config.no_validate = False
        audio_file = tmp_path / "ch01.mp3"
        audio_file.write_bytes(b"fake")

        basic_report.chapters.append(
            ChapterStatus(number=1, title="Ch1", text_file="ch01.txt",
                          final_audio_file=str(audio_file))
        )

        with patch("acx_validator.validate_audio", side_effect=RuntimeError("corrupt")):
            stage_validate(basic_config, basic_report)
            assert len(basic_report.errors) == 1
            assert "corrupt" in basic_report.errors[0]


# ---------------------------------------------------------------------------
# stage_sample — retail sample extraction
# ---------------------------------------------------------------------------

class TestStageSample:
    def test_error_when_no_chapter_1(self, basic_config, basic_report):
        stage_sample(basic_config, basic_report)
        assert any("Chapter 1 not available" in e for e in basic_report.errors)

    def test_error_when_chapter_1_file_missing(self, basic_config, basic_report):
        basic_report.chapters.append(
            ChapterStatus(number=1, title="Ch1", text_file="ch01.txt",
                          final_audio_file="/nonexistent/ch01.mp3")
        )
        stage_sample(basic_config, basic_report)
        assert any("not found" in e for e in basic_report.errors)


# ---------------------------------------------------------------------------
# stage_cleanup
# ---------------------------------------------------------------------------

class TestStageCleanup:
    def test_removes_raw_dir(self, basic_config, basic_report):
        raw_dir = Path(basic_config.output_dir) / "raw_audio"
        raw_dir.mkdir(parents=True)
        (raw_dir / "test.wav").write_bytes(b"data")

        stage_cleanup(basic_config, basic_report)
        assert not raw_dir.exists()

    def test_keeps_raw_when_requested(self, basic_config, basic_report):
        basic_config.keep_intermediate = True
        raw_dir = Path(basic_config.output_dir) / "raw_audio"
        raw_dir.mkdir(parents=True)
        (raw_dir / "test.wav").write_bytes(b"data")

        stage_cleanup(basic_config, basic_report)
        assert raw_dir.exists()

    def test_saves_report_json(self, basic_config, basic_report):
        Path(basic_config.output_dir).mkdir(parents=True, exist_ok=True)
        stage_cleanup(basic_config, basic_report)
        report_path = Path(basic_config.output_dir) / "production_report.json"
        assert report_path.exists()
        data = json.loads(report_path.read_text())
        assert data["title"] == "Test"

    def test_sets_completed_at(self, basic_config, basic_report):
        Path(basic_config.output_dir).mkdir(parents=True, exist_ok=True)
        stage_cleanup(basic_config, basic_report)
        assert basic_report.completed_at is not None


# ---------------------------------------------------------------------------
# run_pipeline — full orchestration
# ---------------------------------------------------------------------------

class TestRunPipeline:
    def test_dry_run_pipeline(self, basic_config):
        """Full pipeline with TTS/postprocess/validate all skipped."""
        report = run_pipeline(basic_config)
        assert len(report.chapters) >= 1
        assert report.total_word_count > 0
        assert report.completed_at is not None

    def test_creates_output_dir(self, basic_config):
        assert not os.path.exists(basic_config.output_dir)
        run_pipeline(basic_config)
        assert os.path.exists(basic_config.output_dir)

    def test_report_saved_on_completion(self, basic_config):
        run_pipeline(basic_config)
        report_path = Path(basic_config.output_dir) / "production_report.json"
        assert report_path.exists()

    def test_report_saved_on_failure(self, basic_config):
        with patch("batch_produce.stage_prep", side_effect=RuntimeError("boom")):
            with pytest.raises(RuntimeError):
                run_pipeline(basic_config)
        report_path = Path(basic_config.output_dir) / "production_report.json"
        assert report_path.exists()
        data = json.loads(report_path.read_text())
        assert any("boom" in e for e in data["errors"])

    def test_verbose_mode(self, basic_config, capsys):
        run_pipeline(basic_config, verbose=True)
        captured = capsys.readouterr()
        assert "STAGE 1" in captured.out


# ---------------------------------------------------------------------------
# print_summary
# ---------------------------------------------------------------------------

class TestPrintSummary:
    def test_prints_summary(self, capsys):
        report = ProductionReport(
            title="Test Book",
            config={},
            started_at="2026-03-18T10:00:00",
            total_word_count=5000,
            total_duration_sec=1800.0,
            acx_passed=5,
            acx_failed=0,
        )
        print_summary(report)
        captured = capsys.readouterr()
        assert "PRODUCTION COMPLETE" in captured.out
        assert "Test Book" in captured.out
        assert "5,000" in captured.out

    def test_prints_errors(self, capsys):
        report = ProductionReport(
            title="Test",
            config={},
            started_at="2026-03-18T10:00:00",
        )
        report.errors.append("Something went wrong")
        print_summary(report)
        captured = capsys.readouterr()
        assert "Something went wrong" in captured.out

    def test_prints_failed_chapters(self, capsys):
        report = ProductionReport(
            title="Test",
            config={},
            started_at="2026-03-18T10:00:00",
            acx_failed=1,
        )
        ch = ChapterStatus(number=3, title="Bad Chapter", text_file="ch03.txt")
        ch.acx_passed = False
        ch.acx_violations = ["loudness: too quiet"]
        report.chapters.append(ch)
        print_summary(report)
        captured = capsys.readouterr()
        assert "Bad Chapter" in captured.out
        assert "too quiet" in captured.out
