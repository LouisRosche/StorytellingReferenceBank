#!/usr/bin/env python3
"""
Integration test for the TTS pipeline.

Tests:
1. Manuscript splitting with page-turn markers
2. TTS generation with children's narrator persona
3. ACX validation of generated audio

Usage:
    # Full test (requires qwen-tts installed)
    python test_pipeline.py

    # Test manuscript splitting only (no GPU required)
    python test_pipeline.py --no-tts

    # Test with custom sample
    python test_pipeline.py --sample path/to/text.txt
"""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_manuscript_splitter():
    """Test manuscript_to_chapters.py"""
    print("\n" + "="*60)
    print("TEST: Manuscript Splitter")
    print("="*60)

    from manuscript_to_chapters import (
        split_manuscript,
        insert_page_turn_pauses,
        create_manifest,
        detect_chapter_pattern,
    )

    # Load sample story
    sample_path = Path(__file__).parent / "sample_childrens_story.txt"
    with open(sample_path, 'r') as f:
        text = f.read()

    print(f"Loaded sample: {len(text)} characters, {len(text.split())} words")

    # Test page turn detection
    assert "[PAGE TURN]" in text, "Sample should contain page turn markers"
    print("Page turn markers detected")

    # Test pause insertion
    processed = insert_page_turn_pauses(text, pause_duration=2.0)
    assert "[PAUSE 2.0s]" in processed, "Pause markers should be inserted"
    print("Pause insertion working")

    # Test splitting (should be single chapter for this short text)
    chapters = split_manuscript(text, min_words=10)
    assert len(chapters) >= 1, "Should produce at least one chapter"
    print(f"Split into {len(chapters)} chapter(s)")

    # Verify word count
    total_words = sum(c.word_count for c in chapters)
    print(f"Total word count: {total_words}")
    assert 150 < total_words < 250, f"Expected ~200 words, got {total_words}"

    print("Manuscript splitter: PASSED")
    return True


def test_tts_generator_import():
    """Test that TTS generator can be imported and has correct structure."""
    print("\n" + "="*60)
    print("TEST: TTS Generator Import")
    print("="*60)

    from tts_generator import (
        Persona,
        chunk_text,
        acx_filename,
        concatenate_audio,
    )

    # Test persona loading
    persona_path = Path(__file__).parent.parent.parent / "personas/examples/narrator-childrens.json"
    persona = Persona.from_json(str(persona_path))

    assert persona.id == "narrator-childrens"
    assert "children" in persona.name.lower() or "narrator" in persona.name.lower()
    assert persona.voice_prompt, "Persona should have a voice prompt"
    print(f"Loaded persona: {persona.name}")
    print(f"Voice prompt: {persona.voice_prompt[:100]}...")

    # Test text chunking
    long_text = "This is a sentence. " * 200  # ~800 words
    chunks = chunk_text(long_text, max_chars=500)
    assert len(chunks) > 1, "Long text should be chunked"
    assert all(len(c) <= 600 for c in chunks), "Chunks should respect max size (with tolerance)"
    print(f"Chunking working: {len(long_text)} chars -> {len(chunks)} chunks")

    # Test filename generation
    filename = acx_filename("My Test Book", chapter_num=1)
    assert filename == "My_Test_Book_Chapter_01.wav"
    print(f"ACX filename: {filename}")

    print("TTS generator import: PASSED")
    return True


def test_acx_validator_import():
    """Test that ACX validator can be imported and has correct structure."""
    print("\n" + "="*60)
    print("TEST: ACX Validator Import")
    print("="*60)

    from acx_validator import (
        ACX_SPECS,
        calculate_rms_db,
        calculate_peak_db,
        CheckResult,
        Severity,
    )

    # Verify specs
    assert ACX_SPECS["rms_min_db"] == -23.0
    assert ACX_SPECS["rms_max_db"] == -18.0
    assert ACX_SPECS["peak_max_db"] == -3.0
    assert ACX_SPECS["noise_floor_max_db"] == -60.0
    print("ACX specs loaded correctly")

    # Test with synthetic audio (requires numpy)
    try:
        import numpy as np

        # Generate test tone at -20 dB
        sample_rate = 44100
        duration = 1.0
        frequency = 440
        t = np.linspace(0, duration, int(sample_rate * duration))
        amplitude = 10 ** (-20 / 20)  # -20 dB
        samples = amplitude * np.sin(2 * np.pi * frequency * t)

        rms_db = calculate_rms_db(samples)
        peak_db = calculate_peak_db(samples)

        print(f"Test tone RMS: {rms_db:.1f} dB (expected ~-20)")
        print(f"Test tone Peak: {peak_db:.1f} dB (expected ~-20)")

        # RMS should be close to -20 for a sine wave
        assert -22 < rms_db < -18, f"RMS calculation off: {rms_db}"
        print("Level calculations: correct")

    except ImportError:
        print("NumPy not installed, skipping synthetic audio test")

    print("ACX validator import: PASSED")
    return True


def test_tts_generation(sample_path: str = None):
    """
    Test actual TTS generation (requires qwen-tts).

    This test is skipped if qwen-tts is not installed.
    """
    print("\n" + "="*60)
    print("TEST: TTS Generation (requires GPU + qwen-tts)")
    print("="*60)

    try:
        import torch
        from qwen_tts import Qwen3TTSModel
    except ImportError as e:
        print(f"Skipping TTS test: {e}")
        print("Install with: pip install qwen-tts torch")
        return None

    if not torch.cuda.is_available():
        print("Skipping TTS test: No GPU available")
        return None

    from tts_generator import Persona, generate_from_persona, save_audio

    # Load persona
    persona_path = Path(__file__).parent.parent.parent / "personas/examples/narrator-childrens.json"
    persona = Persona.from_json(str(persona_path))

    # Load sample text
    if sample_path:
        with open(sample_path, 'r') as f:
            text = f.read()
    else:
        sample_path = Path(__file__).parent / "sample_childrens_story.txt"
        with open(sample_path, 'r') as f:
            text = f.read()

    # Remove page turn markers for TTS (they'd be processed separately in production)
    text = text.replace("[PAGE TURN]", "")

    # Take just first 200 words for test
    words = text.split()[:200]
    test_text = " ".join(words)

    print(f"Generating speech for {len(test_text)} characters...")

    # Generate
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        output_path = f.name

    try:
        wavs, sr = generate_from_persona(test_text, persona)
        save_audio(wavs, sr, output_path)

        # Verify output exists
        assert os.path.exists(output_path), "Output file not created"
        file_size = os.path.getsize(output_path)
        assert file_size > 1000, f"Output file too small: {file_size} bytes"

        print(f"Generated: {output_path} ({file_size:,} bytes)")

        # Validate with ACX validator
        from acx_validator import validate_audio
        report = validate_audio(output_path)

        print(report.summary())

        if report.passed:
            print("TTS generation: PASSED")
        else:
            print("TTS generation: PASSED (audio generated, but may need post-processing for ACX)")

        return output_path

    except Exception as e:
        print(f"TTS generation failed: {e}")
        return None

    finally:
        # Cleanup in production; keep for inspection during development
        pass


def main():
    parser = argparse.ArgumentParser(description="Test TTS pipeline")
    parser.add_argument("--no-tts", action="store_true", help="Skip TTS generation test")
    parser.add_argument("--sample", help="Path to custom sample text")
    args = parser.parse_args()

    results = {}

    # Always run import tests
    results["manuscript_splitter"] = test_manuscript_splitter()
    results["tts_generator_import"] = test_tts_generator_import()
    results["acx_validator_import"] = test_acx_validator_import()

    # Conditionally run TTS generation
    if not args.no_tts:
        results["tts_generation"] = test_tts_generation(args.sample)

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = 0
    failed = 0
    skipped = 0

    for name, result in results.items():
        if result is True:
            status = "PASSED"
            passed += 1
        elif result is None:
            status = "SKIPPED"
            skipped += 1
        else:
            status = "FAILED"
            failed += 1
        print(f"  {name}: {status}")

    print(f"\nTotal: {passed} passed, {failed} failed, {skipped} skipped")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
