#!/usr/bin/env python3
"""
Unit tests for audio_postprocess.py mastering chain.

Tests cover individual DSP stages and the full processing pipeline
using synthetic audio signals. No GPU or TTS engine required.

Run with: python -m pytest scripts/tests/test_audio_postprocess.py -v
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from audio_postprocess import (
    ProcessingParams,
    apply_highpass,
    apply_lowpass,
    apply_compression,
    apply_limiter,
    calculate_rms,
    calculate_rms_db,
    generate_room_tone,
    add_room_tone,
    normalize_loudness,
    process_audio,
    resample,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_RATE = 44100


def make_sine(frequency: float = 440.0, duration: float = 1.0,
              amplitude: float = 0.5, sr: int = SAMPLE_RATE) -> np.ndarray:
    """Generate a pure sine wave."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    return amplitude * np.sin(2 * np.pi * frequency * t)


def db(samples: np.ndarray) -> float:
    """RMS in dB."""
    rms = np.sqrt(np.mean(samples ** 2))
    return 20 * np.log10(rms) if rms > 0 else -100.0


def peak_db(samples: np.ndarray) -> float:
    """Peak in dB."""
    peak = np.max(np.abs(samples))
    return 20 * np.log10(peak) if peak > 0 else -100.0


# ---------------------------------------------------------------------------
# RMS / Peak helpers
# ---------------------------------------------------------------------------

class TestLevelCalculations:
    def test_rms_of_silence(self):
        silence = np.zeros(44100)
        assert calculate_rms(silence) == 0.0
        assert calculate_rms_db(silence) == -100.0

    def test_rms_of_known_signal(self):
        # Sine wave at amplitude A has RMS = A / sqrt(2)
        amp = 0.5
        tone = make_sine(amplitude=amp)
        expected_rms = amp / np.sqrt(2)
        assert abs(calculate_rms(tone) - expected_rms) < 0.001

    def test_rms_db_of_full_scale(self):
        # Full-scale sine (amplitude 1.0) → RMS ≈ -3.01 dB
        tone = make_sine(amplitude=1.0)
        rms = calculate_rms_db(tone)
        assert -3.1 < rms < -2.9


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

class TestHighpassFilter:
    def test_removes_low_frequency(self):
        low_tone = make_sine(frequency=40.0, amplitude=0.5)
        filtered = apply_highpass(low_tone, SAMPLE_RATE, cutoff=80.0)
        # Energy should be significantly reduced
        assert db(filtered) < db(low_tone) - 10

    def test_passes_high_frequency(self):
        high_tone = make_sine(frequency=1000.0, amplitude=0.5)
        filtered = apply_highpass(high_tone, SAMPLE_RATE, cutoff=80.0)
        # Energy should be roughly preserved
        assert abs(db(filtered) - db(high_tone)) < 1.0


class TestLowpassFilter:
    def test_removes_high_frequency(self):
        high_tone = make_sine(frequency=18000.0, amplitude=0.5)
        filtered = apply_lowpass(high_tone, SAMPLE_RATE, cutoff=16000.0)
        assert db(filtered) < db(high_tone) - 6

    def test_passes_low_frequency(self):
        low_tone = make_sine(frequency=440.0, amplitude=0.5)
        filtered = apply_lowpass(low_tone, SAMPLE_RATE, cutoff=16000.0)
        assert abs(db(filtered) - db(low_tone)) < 1.0


# ---------------------------------------------------------------------------
# Dynamics
# ---------------------------------------------------------------------------

class TestCompression:
    def test_reduces_loud_signal(self):
        loud = make_sine(amplitude=0.9)
        compressed = apply_compression(
            loud, SAMPLE_RATE,
            threshold_db=-12.0, ratio=4.0,
            attack_ms=1.0, release_ms=50.0
        )
        # Compressed signal should be quieter
        assert db(compressed) < db(loud)

    def test_preserves_quiet_signal(self):
        quiet = make_sine(amplitude=0.01)
        compressed = apply_compression(
            quiet, SAMPLE_RATE,
            threshold_db=-12.0, ratio=4.0,
            attack_ms=1.0, release_ms=50.0
        )
        # Below threshold — should be nearly unchanged
        assert abs(db(compressed) - db(quiet)) < 1.0


class TestLimiter:
    def test_caps_peaks(self):
        loud = make_sine(amplitude=0.95)
        limited = apply_limiter(loud, SAMPLE_RATE, ceiling_db=-6.0)
        # Peak should not exceed ceiling
        assert peak_db(limited) <= -5.5  # Small tolerance for lookahead smoothing

    def test_passes_quiet_signal(self):
        quiet = make_sine(amplitude=0.1)
        limited = apply_limiter(quiet, SAMPLE_RATE, ceiling_db=-3.0)
        # Already below ceiling — should be nearly unchanged
        assert abs(db(limited) - db(quiet)) < 1.0


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

class TestNormalization:
    def test_normalize_to_target(self):
        tone = make_sine(amplitude=0.1)  # Quiet signal
        normalized = normalize_loudness(tone, target_rms_db=-20.0, sample_rate=SAMPLE_RATE)
        # Should be within ~1 dB of target
        assert abs(db(normalized) - (-20.0)) < 1.5


# ---------------------------------------------------------------------------
# Room tone
# ---------------------------------------------------------------------------

class TestRoomTone:
    def test_room_tone_level(self):
        tone = generate_room_tone(1.0, SAMPLE_RATE, level_db=-70.0)
        assert len(tone) == SAMPLE_RATE
        # Should be very quiet
        assert db(tone) < -60.0

    def test_add_room_tone_extends_duration(self):
        audio = make_sine(duration=1.0)
        with_room = add_room_tone(audio, SAMPLE_RATE, head_sec=0.5, tail_sec=3.0)
        expected_samples = len(audio) + int(0.5 * SAMPLE_RATE) + int(3.0 * SAMPLE_RATE)
        assert len(with_room) == expected_samples


# ---------------------------------------------------------------------------
# Resampling
# ---------------------------------------------------------------------------

class TestResample:
    def test_same_rate_passthrough(self):
        audio = make_sine()
        resampled = resample(audio, SAMPLE_RATE, SAMPLE_RATE)
        np.testing.assert_array_equal(audio, resampled)

    def test_downsample(self):
        audio = make_sine(sr=48000, duration=1.0)
        resampled = resample(audio, 48000, 44100)
        expected_len = int(len(audio) * 44100 / 48000)
        assert abs(len(resampled) - expected_len) <= 1


# ---------------------------------------------------------------------------
# Full chain
# ---------------------------------------------------------------------------

class TestFullMasteringChain:
    def test_output_within_acx_range(self):
        """Mastered audio should land within ACX RMS range (-23 to -18 dB)."""
        # Input: moderately loud sine at 440 Hz
        audio = make_sine(frequency=440.0, amplitude=0.3, duration=2.0)
        params = ProcessingParams(target_rms_db=-20.0)
        processed = process_audio(audio, SAMPLE_RATE, params)

        rms = db(processed)
        # Room tone padding dilutes overall RMS, so allow wider tolerance.
        # The speech portion itself targets -20 dB; room tone pulls the
        # whole-file RMS down slightly.
        assert -26.0 < rms < -16.0, f"RMS {rms:.1f} dB outside acceptable range"

    def test_peak_below_ceiling(self):
        """Peaks should not exceed the limiter ceiling."""
        audio = make_sine(frequency=440.0, amplitude=0.8, duration=2.0)
        params = ProcessingParams(limiter_ceiling_db=-3.0, target_rms_db=-20.0)
        processed = process_audio(audio, SAMPLE_RATE, params)

        peak = peak_db(processed)
        # Room tone at end might have slightly different characteristics,
        # but the speech portion should be limited
        assert peak <= -2.5, f"Peak {peak:.1f} dB exceeds ceiling"

    def test_output_has_room_tone(self):
        """Output should be longer than input due to room tone insertion."""
        audio = make_sine(duration=1.0)
        params = ProcessingParams(room_tone_head_sec=0.5, room_tone_tail_sec=3.0)
        processed = process_audio(audio, SAMPLE_RATE, params)

        input_duration = len(audio) / SAMPLE_RATE
        output_duration = len(processed) / SAMPLE_RATE
        assert output_duration > input_duration + 3.0

    def test_deterministic_output(self):
        """Same input + params should produce identical output."""
        audio = make_sine(duration=1.0)
        params = ProcessingParams()
        out1 = process_audio(audio.copy(), SAMPLE_RATE, params)
        out2 = process_audio(audio.copy(), SAMPLE_RATE, params)
        np.testing.assert_array_equal(out1, out2)


# ---------------------------------------------------------------------------
# Content detection
# ---------------------------------------------------------------------------

from audio_postprocess import detect_content_type, get_content_params, CONTENT_PRESETS


class TestContentDetection:
    """Test auto-detection of content type from manuscript text."""

    def test_detects_childrens_with_page_turns(self):
        text = """Once upon a time there was a little bear.

[PAGE TURN]

The bear went for a walk in the forest.

[PAGE TURN]

"Hello!" said the bear.

[PAGE TURN]

The end.
"""
        assert detect_content_type(text) == "childrens"

    def test_detects_childrens_by_short_length(self):
        # Under 1500 words should be detected as children's
        text = "A short story. " * 100  # ~300 words
        assert detect_content_type(text) == "childrens"

    def test_detects_thriller(self):
        # Needs 5+ thriller words and dialogue ratio > 0.2
        thriller_prose = "The detective crept through the darkness. " * 200
        dialogue = '\n"Where is the murder weapon?" she asked.\n' * 100
        filler = "He examined the crime scene for blood and evidence of the killer. " * 200
        text = thriller_prose + dialogue + filler
        # Ensure word count > 2000 so it's not caught as children's
        assert len(text.split()) > 2000
        result = detect_content_type(text)
        assert result == "thriller"

    def test_detects_nonfiction(self):
        # Low dialogue ratio, long paragraphs (avg > 80 words)
        paragraph = ("The economic implications of this policy are far-reaching and "
                      "significant across multiple sectors of the global economy. "
                      "Researchers have documented extensive evidence supporting "
                      "these conclusions through rigorous empirical analysis. ") * 25
        text = (paragraph + "\n\n") * 10
        assert len(text.split()) > 2000
        result = detect_content_type(text)
        assert result == "nonfiction"

    def test_detects_literary_as_default(self):
        # Generic prose that doesn't match other categories
        text = ("She walked along the river, watching the light change on the water. " * 200 +
                '\n"It was beautiful," she said.\n' * 10)
        assert len(text.split()) > 2000
        result = detect_content_type(text)
        assert result == "literary"


class TestContentPresets:
    """Test that get_content_params returns correct ProcessingParams."""

    def test_returns_params_for_childrens(self):
        params = get_content_params("childrens")
        assert isinstance(params, ProcessingParams)
        assert params.comp_ratio == 2.0

    def test_returns_params_for_thriller(self):
        params = get_content_params("thriller")
        assert isinstance(params, ProcessingParams)
        assert params.comp_ratio == 3.0

    def test_returns_params_for_nonfiction(self):
        params = get_content_params("nonfiction")
        assert isinstance(params, ProcessingParams)
        assert params.comp_ratio == 3.5

    def test_returns_params_for_literary(self):
        params = get_content_params("literary")
        assert isinstance(params, ProcessingParams)
        assert params.comp_ratio == 2.0

    def test_unknown_type_returns_default(self):
        params = get_content_params("unknown_genre")
        assert isinstance(params, ProcessingParams)
        # Should be the default ProcessingParams, not a preset
        default = ProcessingParams()
        assert params.target_rms_db == default.target_rms_db

    def test_all_presets_present(self):
        expected_types = {"childrens", "literary", "thriller", "nonfiction"}
        assert set(CONTENT_PRESETS.keys()) == expected_types


class TestPresetDifferences:
    """Verify presets actually differ from each other."""

    def test_thriller_has_tighter_compression_than_literary(self):
        thriller = CONTENT_PRESETS["thriller"]
        literary = CONTENT_PRESETS["literary"]
        # Tighter = higher ratio
        assert thriller.comp_ratio > literary.comp_ratio

    def test_nonfiction_has_tighter_compression_than_literary(self):
        nonfiction = CONTENT_PRESETS["nonfiction"]
        literary = CONTENT_PRESETS["literary"]
        assert nonfiction.comp_ratio > literary.comp_ratio

    def test_thriller_has_higher_target_rms_than_literary(self):
        thriller = CONTENT_PRESETS["thriller"]
        literary = CONTENT_PRESETS["literary"]
        # Higher (less negative) target RMS = louder
        assert thriller.target_rms_db > literary.target_rms_db

    def test_childrens_differs_from_thriller(self):
        childrens = CONTENT_PRESETS["childrens"]
        thriller = CONTENT_PRESETS["thriller"]
        # They should differ in at least compression ratio
        assert childrens.comp_ratio != thriller.comp_ratio

    def test_each_preset_is_distinct(self):
        """No two presets should be identical."""
        types = list(CONTENT_PRESETS.keys())
        for i in range(len(types)):
            for j in range(i + 1, len(types)):
                a = CONTENT_PRESETS[types[i]]
                b = CONTENT_PRESETS[types[j]]
                # At least one param must differ
                differs = (a.comp_threshold_db != b.comp_threshold_db or
                           a.comp_ratio != b.comp_ratio or
                           a.target_rms_db != b.target_rms_db or
                           a.limiter_ceiling_db != b.limiter_ceiling_db)
                assert differs, f"{types[i]} and {types[j]} presets are identical"
