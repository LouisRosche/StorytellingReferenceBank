"""Tests for persona_regression.py — regression testing for voice personas."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

from persona_regression import (
    load_persona,
    extract_voice_embedding,
    compare_embeddings,
    test_persona as run_test_persona,
    run_regression,
    RegressionResult,
    RegressionReport,
    SIMILARITY_THRESHOLD,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def persona_dir(tmp_path):
    """Create a temp directory with a persona JSON file."""
    persona = {
        "id": "test-narrator",
        "name": "Test Narrator",
        "voice_prompt": "Warm voice",
        "quality": {
            "golden_reference": "test-narrator_golden.wav"
        },
    }
    persona_file = tmp_path / "test-narrator.json"
    persona_file.write_text(json.dumps(persona))
    return tmp_path


@pytest.fixture
def persona_no_golden(tmp_path):
    """Persona without golden reference."""
    persona = {
        "id": "no-ref",
        "name": "No Reference",
        "voice_prompt": "Neutral voice",
    }
    (tmp_path / "no-ref.json").write_text(json.dumps(persona))
    return tmp_path


# ---------------------------------------------------------------------------
# load_persona
# ---------------------------------------------------------------------------


class TestLoadPersona:
    def test_loads_valid_json(self, persona_dir):
        persona = load_persona(persona_dir / "test-narrator.json")
        assert persona["id"] == "test-narrator"
        assert persona["name"] == "Test Narrator"

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_persona(tmp_path / "nonexistent.json")


# ---------------------------------------------------------------------------
# compare_embeddings (cosine similarity)
# ---------------------------------------------------------------------------


class TestCompareEmbeddings:
    def test_identical_vectors(self):
        v = np.array([1.0, 2.0, 3.0])
        assert compare_embeddings(v, v) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        v1 = np.array([1.0, 0.0])
        v2 = np.array([0.0, 1.0])
        assert compare_embeddings(v1, v2) == pytest.approx(0.0)

    def test_opposite_vectors(self):
        v = np.array([1.0, 2.0, 3.0])
        assert compare_embeddings(v, -v) == pytest.approx(-1.0)

    def test_zero_vector(self):
        v = np.array([1.0, 2.0])
        zero = np.array([0.0, 0.0])
        assert compare_embeddings(v, zero) == 0.0
        assert compare_embeddings(zero, v) == 0.0

    def test_different_magnitudes_same_direction(self):
        v1 = np.array([1.0, 2.0, 3.0])
        v2 = np.array([2.0, 4.0, 6.0])
        assert compare_embeddings(v1, v2) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# extract_voice_embedding
# ---------------------------------------------------------------------------


class TestExtractVoiceEmbedding:
    def test_no_libraries_returns_none(self, tmp_path):
        dummy_wav = tmp_path / "dummy.wav"
        dummy_wav.touch()
        with patch("persona_regression.RESEMBLYZER_AVAILABLE", False), \
             patch("persona_regression.LIBROSA_AVAILABLE", False):
            result = extract_voice_embedding(dummy_wav)
        assert result is None


# ---------------------------------------------------------------------------
# test_persona
# ---------------------------------------------------------------------------


class TestTestPersona:
    def test_skips_when_no_golden_ref(self, persona_no_golden, tmp_path):
        result = run_test_persona(
            persona_no_golden / "no-ref.json",
            golden_dir=tmp_path,
            test_dir=tmp_path,
        )
        assert result.passed is True
        assert "skipped" in result.message.lower()

    def test_skips_when_golden_file_missing(self, persona_dir, tmp_path):
        result = run_test_persona(
            persona_dir / "test-narrator.json",
            golden_dir=tmp_path,  # no golden file here
            test_dir=tmp_path,
        )
        assert result.passed is True
        assert "not found" in result.message.lower()

    def test_fails_when_test_audio_missing(self, persona_dir, tmp_path):
        # Create golden file but not test file
        golden_dir = tmp_path / "golden"
        golden_dir.mkdir()
        (golden_dir / "test-narrator_golden.wav").touch()
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        result = run_test_persona(
            persona_dir / "test-narrator.json",
            golden_dir=golden_dir,
            test_dir=test_dir,
        )
        assert result.passed is False
        assert "not found" in result.message.lower()

    def test_skips_when_no_audio_library(self, persona_dir, tmp_path):
        golden_dir = tmp_path / "golden"
        golden_dir.mkdir()
        (golden_dir / "test-narrator_golden.wav").touch()
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        (test_dir / "test-narrator_test.wav").touch()
        with patch("persona_regression.RESEMBLYZER_AVAILABLE", False), \
             patch("persona_regression.LIBROSA_AVAILABLE", False):
            result = run_test_persona(
                persona_dir / "test-narrator.json",
                golden_dir=golden_dir,
                test_dir=test_dir,
            )
        assert result.passed is True
        assert "skipped" in result.message.lower()


# ---------------------------------------------------------------------------
# run_regression
# ---------------------------------------------------------------------------


class TestRunRegression:
    def test_empty_directory(self, tmp_path):
        report = run_regression(
            personas_dir=tmp_path,
            golden_dir=tmp_path,
            test_dir=tmp_path,
        )
        assert report.total == 0
        assert report.passed == 0
        assert report.failed == 0

    def test_single_persona_no_golden(self, persona_no_golden, tmp_path):
        report = run_regression(
            personas_dir=persona_no_golden,
            golden_dir=tmp_path,
            test_dir=tmp_path,
        )
        assert report.total == 1
        assert report.skipped == 1

    def test_filter_by_persona_id(self, persona_dir, tmp_path):
        report = run_regression(
            personas_dir=persona_dir,
            golden_dir=tmp_path,
            test_dir=tmp_path,
            persona_ids=["nonexistent-id"],
        )
        assert report.total == 0

    def test_success_rate_empty(self):
        report = RegressionReport(total=0, passed=0, failed=0, skipped=0, results=[])
        assert report.success_rate == 0.0

    def test_success_rate_calculation(self):
        report = RegressionReport(total=4, passed=3, failed=1, skipped=0, results=[])
        assert report.success_rate == pytest.approx(0.75)
