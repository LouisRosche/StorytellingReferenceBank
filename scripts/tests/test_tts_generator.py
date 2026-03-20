"""Tests for tts_generator.py — testable functions without GPU/TTS dependencies."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

from tts_generator import Persona, chunk_text, acx_filename, concatenate_audio


# ---------------------------------------------------------------------------
# Persona.from_json
# ---------------------------------------------------------------------------


class TestPersonaFromJson:
    def test_loads_full_persona(self, tmp_path):
        data = {
            "id": "literary-narrator",
            "name": "Literary Narrator",
            "voice_prompt": "Deep, resonant voice",
            "character_context": "Experienced storyteller",
            "model_variant": "1.7B-VoiceDesign",
            "provider": "openai",
            "reference_audio": {
                "path": "ref.wav",
                "transcript": "Hello world",
            },
        }
        p = tmp_path / "persona.json"
        p.write_text(json.dumps(data))
        persona = Persona.from_json(str(p))
        assert persona.id == "literary-narrator"
        assert persona.name == "Literary Narrator"
        assert persona.voice_prompt == "Deep, resonant voice"
        assert persona.character_context == "Experienced storyteller"
        assert persona.reference_audio_path == "ref.wav"
        assert persona.reference_audio_transcript == "Hello world"
        assert persona.model_variant == "1.7B-VoiceDesign"
        assert persona.provider == "openai"

    def test_loads_minimal_persona(self, tmp_path):
        data = {"id": "simple", "name": "Simple", "voice_prompt": "Neutral"}
        p = tmp_path / "simple.json"
        p.write_text(json.dumps(data))
        persona = Persona.from_json(str(p))
        assert persona.id == "simple"
        assert persona.model_variant == "1.7B-Base"  # default
        assert persona.provider is None
        assert persona.reference_audio_path is None

    def test_missing_required_field_raises(self, tmp_path):
        data = {"name": "No ID", "voice_prompt": "Voice"}
        p = tmp_path / "bad.json"
        p.write_text(json.dumps(data))
        with pytest.raises(KeyError):
            Persona.from_json(str(p))

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            Persona.from_json(str(tmp_path / "nonexistent.json"))


# ---------------------------------------------------------------------------
# chunk_text
# ---------------------------------------------------------------------------


class TestChunkText:
    def test_short_text_single_chunk(self):
        text = "This is short."
        result = chunk_text(text, max_chars=100)
        assert result == [text]

    def test_splits_on_sentence_boundary(self):
        text = "First sentence. Second sentence. Third sentence."
        result = chunk_text(text, max_chars=30)
        assert len(result) >= 2
        # Each chunk should end at sentence boundary
        for chunk in result:
            assert chunk.strip().endswith(".")

    def test_respects_max_chars(self):
        sentences = ["Sentence number one. " * 5] * 10
        text = " ".join(sentences)
        result = chunk_text(text, max_chars=200)
        for chunk in result:
            assert len(chunk) <= 200 + 50  # Allow some tolerance for sentence boundary

    def test_empty_text(self):
        assert chunk_text("", max_chars=100) == [""]

    def test_single_long_sentence(self):
        text = "A " * 500  # Single sentence without period
        result = chunk_text(text.strip(), max_chars=100)
        # Should still produce at least one chunk
        assert len(result) >= 1

    def test_default_max_chars(self):
        text = "Short text."
        result = chunk_text(text)
        assert result == [text]


# ---------------------------------------------------------------------------
# acx_filename
# ---------------------------------------------------------------------------


class TestAcxFilename:
    def test_chapter_number(self):
        result = acx_filename("My Book", chapter_num=3)
        assert result == "My_Book_Chapter_03.wav"

    def test_chapter_name(self):
        result = acx_filename("My Book", chapter_name="Opening Credits")
        assert result == "My_Book_Opening_Credits.wav"

    def test_title_only(self):
        result = acx_filename("My Book")
        assert result == "My_Book.wav"

    def test_special_characters_stripped(self):
        result = acx_filename("Book: A Novel!", chapter_num=1)
        assert ":" not in result
        assert "!" not in result

    def test_chapter_number_zero_padded(self):
        result = acx_filename("Title", chapter_num=1)
        assert "Chapter_01" in result
        result = acx_filename("Title", chapter_num=12)
        assert "Chapter_12" in result

    def test_number_takes_precedence(self):
        # When both are provided, chapter_num should be used
        result = acx_filename("Title", chapter_num=5, chapter_name="Ignored")
        assert "Chapter_05" in result


# ---------------------------------------------------------------------------
# concatenate_audio
# ---------------------------------------------------------------------------


class TestConcatenateAudio:
    def test_single_chunk(self):
        audio = np.ones(1000)
        result, sr = concatenate_audio([([audio], 44100)])
        assert sr == 44100
        np.testing.assert_array_equal(result[0], audio)

    def test_two_chunks_with_gap(self):
        sr = 44100
        audio1 = np.ones(1000)
        audio2 = np.ones(500)
        result, result_sr = concatenate_audio(
            [([audio1], sr), ([audio2], sr)],
            gap_seconds=0.1,
        )
        assert result_sr == sr
        gap_samples = int(sr * 0.1)
        expected_len = 1000 + gap_samples + 500
        assert len(result[0]) == expected_len

    def test_gap_is_silence(self):
        sr = 44100
        audio1 = np.ones(100)
        audio2 = np.ones(100)
        result, _ = concatenate_audio(
            [([audio1], sr), ([audio2], sr)],
            gap_seconds=0.5,
        )
        gap_start = 100
        gap_end = 100 + int(sr * 0.5)
        gap_region = result[0][gap_start:gap_end]
        np.testing.assert_array_equal(gap_region, np.zeros(len(gap_region)))

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="No audio"):
            concatenate_audio([])

    def test_no_gap(self):
        sr = 44100
        audio1 = np.ones(100)
        audio2 = np.ones(200)
        result, _ = concatenate_audio(
            [([audio1], sr), ([audio2], sr)],
            gap_seconds=0.0,
        )
        assert len(result[0]) == 300
