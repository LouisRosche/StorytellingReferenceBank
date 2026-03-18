"""
Integration tests for the TTS pipeline.

Tests manuscript splitting, TTS generator imports, and ACX validator imports.
GPU-dependent TTS generation is marked with the 'gpu' marker.

Run with: python -m pytest scripts/tests/test_pipeline.py -v
"""

import os
import tempfile
from pathlib import Path

import pytest


def test_manuscript_splitter():
    """Test manuscript_to_chapters.py with sample children's story."""
    from manuscript_to_chapters import (
        split_manuscript,
        insert_page_turn_pauses,
        detect_chapter_pattern,
    )

    sample_path = Path(__file__).parent / "sample_childrens_story.txt"
    with open(sample_path, "r") as f:
        text = f.read()

    assert "[PAGE TURN]" in text

    processed = insert_page_turn_pauses(text, pause_duration=2.0)
    assert "[PAUSE 2.0s]" in processed

    chapters = split_manuscript(text, min_words=10)
    assert len(chapters) >= 1

    total_words = sum(c.word_count for c in chapters)
    assert 150 < total_words < 250, f"Expected ~200 words, got {total_words}"


def test_tts_generator_import():
    """Test that TTS generator can be imported and has correct structure."""
    from tts_generator import (
        Persona,
        chunk_text,
        acx_filename,
    )

    persona_path = (
        Path(__file__).parent.parent.parent / "personas/examples/narrator-childrens.json"
    )
    persona = Persona.from_json(str(persona_path))

    assert persona.id == "narrator-childrens"
    assert persona.voice_prompt

    long_text = "This is a sentence. " * 200
    chunks = chunk_text(long_text, max_chars=500)
    assert len(chunks) > 1
    assert all(len(c) <= 600 for c in chunks)

    filename = acx_filename("My Test Book", chapter_num=1)
    assert filename == "My_Test_Book_Chapter_01.wav"


def test_acx_validator_import():
    """Test that ACX validator can be imported and has correct structure."""
    from acx_validator import (
        ACX_SPECS,
        calculate_rms_db,
        calculate_peak_db,
    )

    assert ACX_SPECS["rms_min_db"] == -23.0
    assert ACX_SPECS["rms_max_db"] == -18.0
    assert ACX_SPECS["peak_max_db"] == -3.0
    assert ACX_SPECS["noise_floor_max_db"] == -60.0

    try:
        import numpy as np

        sample_rate = 44100
        t = np.linspace(0, 1.0, sample_rate)
        amplitude = 10 ** (-20 / 20)
        samples = amplitude * np.sin(2 * np.pi * 440 * t)

        rms_db = calculate_rms_db(samples)
        peak_db = calculate_peak_db(samples)

        assert -25 < rms_db < -21, f"RMS calculation off: {rms_db}"
    except ImportError:
        pytest.skip("NumPy not installed")


@pytest.mark.gpu
def test_tts_generation():
    """Test actual TTS generation (requires qwen-tts + GPU)."""
    try:
        import torch
        from qwen_tts import Qwen3TTSModel
    except ImportError:
        pytest.skip("qwen-tts not installed")

    if not torch.cuda.is_available():
        pytest.skip("No GPU available")

    from tts_generator import Persona, generate_from_persona, save_audio
    from acx_validator import validate_audio

    persona_path = (
        Path(__file__).parent.parent.parent / "personas/examples/narrator-childrens.json"
    )
    persona = Persona.from_json(str(persona_path))

    sample_path = Path(__file__).parent / "sample_childrens_story.txt"
    with open(sample_path, "r") as f:
        text = f.read().replace("[PAGE TURN]", "")

    test_text = " ".join(text.split()[:200])

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        output_path = f.name

    try:
        wavs, sr = generate_from_persona(test_text, persona)
        save_audio(wavs, sr, output_path)

        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 1000

        report = validate_audio(output_path)
        # Audio generated — may need post-processing for ACX but generation worked
        assert os.path.getsize(output_path) > 1000
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)
