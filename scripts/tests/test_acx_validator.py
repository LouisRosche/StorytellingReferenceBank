"""
Unit tests for acx_validator.py ACX compliance checker.

Tests cover level calculations, spec enforcement, and report generation
using synthetic audio. No GPU or TTS engine required.

Run with: python -m pytest scripts/tests/test_acx_validator.py -v
"""

import os
import tempfile

import numpy as np

from acx_validator import (
    ACX_SPECS,
    Severity,
    CheckResult,
    ValidationReport,
    calculate_rms_db,
    calculate_peak_db,
    calculate_noise_floor_db,
    validate_audio,
)
from conftest import SAMPLE_RATE, make_sine, write_wav


# ---------------------------------------------------------------------------
# Level calculations
# ---------------------------------------------------------------------------

class TestCalculateRmsDb:
    def test_silence(self):
        silence = np.zeros(44100)
        assert calculate_rms_db(silence) == -100.0

    def test_known_level(self):
        amp = 0.1
        tone = make_sine(amplitude=amp)
        rms = calculate_rms_db(tone)
        expected = 20 * np.log10(amp / np.sqrt(2))
        assert abs(rms - expected) < 0.1


class TestCalculatePeakDb:
    def test_silence(self):
        silence = np.zeros(44100)
        assert calculate_peak_db(silence) == -100.0

    def test_known_peak(self):
        amp = 0.5
        tone = make_sine(amplitude=amp)
        peak = calculate_peak_db(tone)
        expected = 20 * np.log10(amp)
        assert abs(peak - expected) < 0.1

    def test_full_scale(self):
        tone = make_sine(amplitude=1.0)
        peak = calculate_peak_db(tone)
        assert abs(peak) < 0.1


class TestNoiseFloor:
    def test_quiet_signal(self):
        np.random.seed(0)
        quiet_noise = np.random.randn(44100 * 2) * 1e-4
        nf = calculate_noise_floor_db(quiet_noise, SAMPLE_RATE)
        assert nf < -60.0

    def test_loud_signal_noise_floor(self):
        loud = make_sine(amplitude=0.5, duration=1.0)
        quiet = np.random.randn(44100) * 1e-4
        mixed = np.concatenate([loud, quiet])
        nf = calculate_noise_floor_db(mixed, SAMPLE_RATE)
        assert nf < -50.0


# ---------------------------------------------------------------------------
# ACX spec constants
# ---------------------------------------------------------------------------

class TestACXSpecs:
    def test_rms_range(self):
        assert ACX_SPECS["rms_min_db"] == -23.0
        assert ACX_SPECS["rms_max_db"] == -18.0

    def test_peak_max(self):
        assert ACX_SPECS["peak_max_db"] == -3.0

    def test_noise_floor(self):
        assert ACX_SPECS["noise_floor_max_db"] == -60.0

    def test_format_specs(self):
        assert ACX_SPECS["sample_rate_hz"] == 44100
        assert ACX_SPECS["bit_rate_kbps"] == 192
        assert ACX_SPECS["channels"] == 1


# ---------------------------------------------------------------------------
# CheckResult and ValidationReport
# ---------------------------------------------------------------------------

class TestCheckResult:
    def test_to_dict(self):
        cr = CheckResult(
            name="RMS Level",
            severity=Severity.PASS,
            message="OK",
            actual_value=-20.0,
            expected_value="-23 to -18 dB",
        )
        d = cr.to_dict()
        assert d["name"] == "RMS Level"
        assert d["severity"] == "pass"
        assert d["actual_value"] == -20.0


class TestValidationReport:
    def test_starts_passing(self):
        report = ValidationReport(file_path="test.wav", passed=True)
        assert report.passed is True

    def test_fail_on_error(self):
        report = ValidationReport(file_path="test.wav", passed=True)
        report.add_error("File not found")
        assert report.passed is False

    def test_fail_on_check_failure(self):
        report = ValidationReport(file_path="test.wav", passed=True)
        report.add_check(CheckResult("test", Severity.FAIL, "bad"))
        assert report.passed is False

    def test_pass_on_warning(self):
        report = ValidationReport(file_path="test.wav", passed=True)
        report.add_check(CheckResult("test", Severity.WARNING, "meh"))
        assert report.passed is True

    def test_to_dict(self):
        report = ValidationReport(file_path="test.wav", passed=True)
        report.add_check(CheckResult("test", Severity.PASS, "good"))
        d = report.to_dict()
        assert d["passed"] is True
        assert len(d["checks"]) == 1

    def test_summary_text(self):
        report = ValidationReport(file_path="test.wav", passed=True)
        report.add_check(CheckResult("test", Severity.PASS, "good"))
        text = report.summary()
        assert "test.wav" in text
        assert "PASSED" in text


# ---------------------------------------------------------------------------
# Full file validation
# ---------------------------------------------------------------------------

class TestValidateAudio:
    def test_file_not_found(self):
        report = validate_audio("/nonexistent/file.wav")
        assert report.passed is False
        assert any("not found" in e.lower() for e in report.errors)

    def test_unsupported_format(self):
        fd, path = tempfile.mkstemp(suffix=".ogg")
        os.close(fd)
        try:
            report = validate_audio(path)
            assert report.passed is False
        finally:
            os.unlink(path)

    def test_compliant_audio_passes(self):
        """A properly mastered signal should pass validation."""
        target_rms = 10 ** (-20.0 / 20)
        target_amp = target_rms * np.sqrt(2)

        silence_head = np.zeros(int(0.5 * SAMPLE_RATE))
        tone = make_sine(amplitude=target_amp, duration=4.0)
        silence_tail = np.zeros(int(1.0 * SAMPLE_RATE))
        audio = np.concatenate([silence_head, tone, silence_tail])

        path = write_wav(audio)
        try:
            report = validate_audio(path)
            rms_checks = [c for c in report.checks if c.name == "RMS Level"]
            peak_checks = [c for c in report.checks if c.name == "Peak Level"]
            assert len(rms_checks) == 1
            assert rms_checks[0].severity == Severity.PASS
            assert len(peak_checks) == 1
            assert peak_checks[0].severity == Severity.PASS
        finally:
            os.unlink(path)

    def test_too_loud_fails_rms(self):
        """Audio above -18 dB RMS should fail."""
        loud = make_sine(amplitude=0.8, duration=2.0)
        path = write_wav(loud)
        try:
            report = validate_audio(path)
            rms_checks = [c for c in report.checks if c.name == "RMS Level"]
            assert rms_checks[0].severity == Severity.FAIL
            assert "loud" in rms_checks[0].message.lower()
        finally:
            os.unlink(path)

    def test_too_quiet_fails_rms(self):
        """Audio below -23 dB RMS should fail."""
        quiet = make_sine(amplitude=0.01, duration=2.0)
        path = write_wav(quiet)
        try:
            report = validate_audio(path)
            rms_checks = [c for c in report.checks if c.name == "RMS Level"]
            assert rms_checks[0].severity == Severity.FAIL
            assert "quiet" in rms_checks[0].message.lower()
        finally:
            os.unlink(path)

    def test_clipping_fails_peak(self):
        """Audio with peaks above -3 dB should fail peak check."""
        loud = make_sine(amplitude=0.95, duration=2.0)
        path = write_wav(loud)
        try:
            report = validate_audio(path)
            peak_checks = [c for c in report.checks if c.name == "Peak Level"]
            assert peak_checks[0].severity == Severity.FAIL
        finally:
            os.unlink(path)

    def test_wrong_sample_rate_fails(self):
        """Non-44.1kHz audio should fail sample rate check."""
        tone = make_sine(sr=22050, duration=2.0)
        path = write_wav(tone, sr=22050)
        try:
            report = validate_audio(path)
            sr_checks = [c for c in report.checks if c.name == "Sample Rate"]
            assert sr_checks[0].severity == Severity.FAIL
        finally:
            os.unlink(path)

    def test_report_metadata(self):
        """Validation should populate metadata fields."""
        tone = make_sine(duration=2.0)
        path = write_wav(tone)
        try:
            report = validate_audio(path)
            assert "rms_db" in report.metadata
            assert "peak_db" in report.metadata
            assert "noise_floor_db" in report.metadata
        finally:
            os.unlink(path)
