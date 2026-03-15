#!/usr/bin/env python3
"""
ACX/Audible audio compliance validator.

Verifies audiobook files meet ACX technical specifications:
- RMS levels: -23 dB to -18 dB
- Peak levels: -3 dB maximum
- Noise floor: -60 dB RMS maximum
- Format: 192 kbps CBR MP3, 44.1 kHz, mono

Usage:
    # Validate single file
    python acx_validator.py audio.mp3

    # Validate directory of files
    python acx_validator.py audiobook_folder/

    # Output JSON report
    python acx_validator.py audio.mp3 --json

    # Strict mode (fail on warnings)
    python acx_validator.py audio.mp3 --strict
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any

# Optional high-quality backends
try:
    import pyloudnorm as pyln
    PYLOUDNORM_AVAILABLE = True
except ImportError:
    PYLOUDNORM_AVAILABLE = False

try:
    from silero_vad import load_silero_vad, get_speech_timestamps
    import torch
    SILERO_VAD_AVAILABLE = True
except ImportError:
    SILERO_VAD_AVAILABLE = False

# ACX Specifications
ACX_SPECS = {
    "rms_min_db": -23.0,
    "rms_max_db": -18.0,
    "peak_max_db": -3.0,
    "noise_floor_max_db": -60.0,
    "sample_rate_hz": 44100,
    "bit_rate_kbps": 192,
    "channels": 1,  # Mono
    "format": "mp3",
    "room_tone_start_min_sec": 0.5,
    "room_tone_start_max_sec": 1.0,
    "room_tone_end_max_sec": 5.0,
}


class Severity(Enum):
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


@dataclass
class CheckResult:
    """Result of a single compliance check."""
    name: str
    severity: Severity
    message: str
    actual_value: Optional[Any] = None
    expected_value: Optional[Any] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "severity": self.severity.value,
            "message": self.message,
            "actual_value": self.actual_value,
            "expected_value": self.expected_value,
        }


@dataclass
class ValidationReport:
    """Complete validation report for an audio file."""
    file_path: str
    passed: bool
    checks: List[CheckResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_check(self, result: CheckResult):
        self.checks.append(result)
        if result.severity == Severity.FAIL:
            self.passed = False

    def add_error(self, error: str):
        self.errors.append(error)
        self.passed = False

    def to_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "passed": self.passed,
            "checks": [c.to_dict() for c in self.checks],
            "errors": self.errors,
            "metadata": self.metadata,
        }

    def summary(self) -> str:
        """Human-readable summary."""
        lines = [f"\n{'='*60}", f"File: {self.file_path}", "="*60]

        if self.errors:
            lines.append("\nERRORS:")
            for e in self.errors:
                lines.append(f"  - {e}")

        # Group by severity
        fails = [c for c in self.checks if c.severity == Severity.FAIL]
        warnings = [c for c in self.checks if c.severity == Severity.WARNING]
        passes = [c for c in self.checks if c.severity == Severity.PASS]

        if fails:
            lines.append("\nFAILED CHECKS:")
            for c in fails:
                lines.append(f"  [FAIL] {c.name}: {c.message}")
                if c.actual_value is not None:
                    lines.append(f"         Actual: {c.actual_value}, Expected: {c.expected_value}")

        if warnings:
            lines.append("\nWARNINGS:")
            for c in warnings:
                lines.append(f"  [WARN] {c.name}: {c.message}")

        if passes:
            lines.append(f"\nPASSED: {len(passes)} checks")

        # Overall result
        status = "PASSED" if self.passed else "FAILED"
        lines.append(f"\nOVERALL: {status}")
        lines.append("="*60)

        return "\n".join(lines)


def load_audio(file_path: str):
    """
    Load audio file and return samples + metadata.

    Returns:
        Tuple of (samples_array, sample_rate, metadata_dict)
    """
    try:
        import soundfile as sf
        import numpy as np
    except ImportError:
        raise ImportError("Install dependencies: pip install soundfile numpy")

    # Get file info first
    info = sf.info(file_path)
    metadata = {
        "sample_rate": info.samplerate,
        "channels": info.channels,
        "duration_seconds": info.duration,
        "format": info.format,
        "subtype": info.subtype,
    }

    # Load audio data
    samples, sr = sf.read(file_path, dtype='float64')

    # Convert stereo to mono if needed for analysis
    if len(samples.shape) > 1:
        samples = np.mean(samples, axis=1)

    return samples, sr, metadata


def get_mp3_info(file_path: str) -> Dict[str, Any]:
    """Get MP3-specific metadata using pydub."""
    try:
        from pydub import AudioSegment
        from pydub.utils import mediainfo
    except ImportError:
        return {}

    try:
        info = mediainfo(file_path)
        audio = AudioSegment.from_file(file_path)

        return {
            "bit_rate_kbps": int(info.get("bit_rate", 0)) // 1000,
            "codec": info.get("codec_name", ""),
            "duration_ms": len(audio),
            "channels": audio.channels,
            "sample_rate": audio.frame_rate,
        }
    except Exception:
        return {}


def calculate_lufs(samples, sample_rate: int) -> Optional[float]:
    """
    Calculate integrated loudness in LUFS (ITU-R BS.1770-4).

    Returns None if pyloudnorm is not available.
    """
    if not PYLOUDNORM_AVAILABLE:
        return None
    import numpy as np
    meter = pyln.Meter(sample_rate)
    try:
        return meter.integrated_loudness(samples)
    except Exception:
        return None


def calculate_rms_db(samples) -> float:
    """Calculate RMS level in dB."""
    import numpy as np

    # RMS = sqrt(mean(samples^2))
    rms = np.sqrt(np.mean(samples ** 2))

    # Convert to dB (reference = 1.0 for normalized float audio)
    if rms > 0:
        return 20 * np.log10(rms)
    return -100.0  # Silence


def calculate_peak_db(samples) -> float:
    """Calculate peak level in dB."""
    import numpy as np

    peak = np.max(np.abs(samples))
    if peak > 0:
        return 20 * np.log10(peak)
    return -100.0


def calculate_noise_floor_db(samples, sample_rate: int, silence_threshold_db: float = -40.0) -> float:
    """
    Estimate noise floor from quiet sections.

    Finds sections below silence threshold and measures their RMS.
    """
    import numpy as np

    # Window size for analysis (100ms)
    window_size = int(sample_rate * 0.1)

    if len(samples) < window_size:
        return calculate_rms_db(samples)

    # Calculate RMS for each window
    num_windows = len(samples) // window_size
    window_rms = []

    for i in range(num_windows):
        start = i * window_size
        end = start + window_size
        window = samples[start:end]
        rms = np.sqrt(np.mean(window ** 2))
        if rms > 0:
            window_rms.append(20 * np.log10(rms))

    if not window_rms:
        return -100.0

    # Find quietest windows (bottom 10% or below threshold)
    window_rms = np.array(window_rms)
    quiet_threshold = max(np.percentile(window_rms, 10), silence_threshold_db)
    quiet_windows = window_rms[window_rms < quiet_threshold]

    if len(quiet_windows) > 0:
        return float(np.mean(quiet_windows))

    # If no quiet sections, use minimum window
    return float(np.min(window_rms))


def check_room_tone_vad(samples, sample_rate: int) -> tuple:
    """
    Neural voice activity detection for room tone measurement (silero-vad).

    Uses a pre-trained neural network to precisely detect speech boundaries,
    giving much more accurate room tone measurements than energy thresholds.

    Returns:
        Tuple of (start_silence_seconds, end_silence_seconds)
    """
    # Silero VAD requires 16kHz input
    if sample_rate != 16000:
        from scipy.signal import resample as scipy_resample
        num_samples_16k = int(len(samples) * 16000 / sample_rate)
        samples_16k = scipy_resample(samples, num_samples_16k)
    else:
        samples_16k = samples

    audio_tensor = torch.tensor(samples_16k, dtype=torch.float32)
    model = load_silero_vad()
    speech_timestamps = get_speech_timestamps(audio_tensor, model, sampling_rate=16000)

    duration_16k = len(samples_16k) / 16000

    if not speech_timestamps:
        # No speech detected — entire file is silence
        return duration_16k, 0.0

    # Start silence = time before first speech
    first_speech_sec = speech_timestamps[0]['start'] / 16000
    # End silence = time after last speech
    last_speech_end_sec = speech_timestamps[-1]['end'] / 16000
    end_silence = duration_16k - last_speech_end_sec

    return first_speech_sec, max(0.0, end_silence)


def check_room_tone(samples, sample_rate: int) -> tuple:
    """
    Check for room tone at start and end.

    Uses silero-vad neural network when available for precise speech
    boundary detection. Falls back to energy threshold otherwise.

    Returns:
        Tuple of (start_silence_seconds, end_silence_seconds)
    """
    import numpy as np

    # Prefer neural VAD when available
    if SILERO_VAD_AVAILABLE:
        try:
            return check_room_tone_vad(samples, sample_rate)
        except Exception:
            pass  # Fall through to energy-based detection

    # Fallback: energy threshold detection
    silence_threshold = 10 ** (-40 / 20)
    window_size = int(sample_rate * 0.01)

    # Check start
    start_silence = 0.0
    for i in range(0, min(len(samples), sample_rate * 2), window_size):
        window = samples[i:i + window_size]
        if np.max(np.abs(window)) < silence_threshold:
            start_silence = (i + window_size) / sample_rate
        else:
            break

    # Check end
    end_silence = 0.0
    for i in range(len(samples), max(0, len(samples) - sample_rate * 6), -window_size):
        window = samples[max(0, i - window_size):i]
        if len(window) > 0 and np.max(np.abs(window)) < silence_threshold:
            end_silence = (len(samples) - i + window_size) / sample_rate
        else:
            break

    return start_silence, end_silence


def validate_audio(file_path: str, strict: bool = False) -> ValidationReport:
    """
    Validate audio file against ACX specifications.

    Args:
        file_path: Path to audio file
        strict: If True, treat warnings as failures

    Returns:
        ValidationReport with all check results
    """
    report = ValidationReport(file_path=file_path, passed=True)

    # Check file exists
    if not os.path.exists(file_path):
        report.add_error(f"File not found: {file_path}")
        return report

    # Check file extension
    ext = Path(file_path).suffix.lower()
    if ext not in ['.mp3', '.wav', '.flac']:
        report.add_error(f"Unsupported format: {ext}")
        return report

    # Load audio
    try:
        samples, sr, metadata = load_audio(file_path)
        report.metadata = metadata
    except Exception as e:
        report.add_error(f"Failed to load audio: {e}")
        return report

    # Get MP3-specific info if applicable
    if ext == '.mp3':
        mp3_info = get_mp3_info(file_path)
        report.metadata.update(mp3_info)

    # === FORMAT CHECKS ===

    # Sample rate
    if sr == ACX_SPECS["sample_rate_hz"]:
        report.add_check(CheckResult(
            name="Sample Rate",
            severity=Severity.PASS,
            message=f"Correct sample rate: {sr} Hz",
            actual_value=sr,
            expected_value=ACX_SPECS["sample_rate_hz"],
        ))
    else:
        report.add_check(CheckResult(
            name="Sample Rate",
            severity=Severity.FAIL,
            message=f"Incorrect sample rate: {sr} Hz (expected {ACX_SPECS['sample_rate_hz']} Hz)",
            actual_value=sr,
            expected_value=ACX_SPECS["sample_rate_hz"],
        ))

    # Channels
    channels = metadata.get("channels", 1)
    if channels == ACX_SPECS["channels"]:
        report.add_check(CheckResult(
            name="Channels",
            severity=Severity.PASS,
            message="Mono audio",
            actual_value=channels,
            expected_value=ACX_SPECS["channels"],
        ))
    else:
        severity = Severity.FAIL if strict else Severity.WARNING
        report.add_check(CheckResult(
            name="Channels",
            severity=severity,
            message=f"Expected mono, got {channels} channels",
            actual_value=channels,
            expected_value=ACX_SPECS["channels"],
        ))

    # Bit rate (MP3 only)
    if ext == '.mp3':
        bit_rate = report.metadata.get("bit_rate_kbps", 0)
        if bit_rate >= ACX_SPECS["bit_rate_kbps"]:
            report.add_check(CheckResult(
                name="Bit Rate",
                severity=Severity.PASS,
                message=f"Bit rate OK: {bit_rate} kbps",
                actual_value=bit_rate,
                expected_value=ACX_SPECS["bit_rate_kbps"],
            ))
        else:
            report.add_check(CheckResult(
                name="Bit Rate",
                severity=Severity.FAIL,
                message=f"Bit rate too low: {bit_rate} kbps (minimum {ACX_SPECS['bit_rate_kbps']} kbps)",
                actual_value=bit_rate,
                expected_value=ACX_SPECS["bit_rate_kbps"],
            ))

    # === LEVEL CHECKS ===

    # RMS Level
    rms_db = calculate_rms_db(samples)
    report.metadata["rms_db"] = round(rms_db, 2)

    if ACX_SPECS["rms_min_db"] <= rms_db <= ACX_SPECS["rms_max_db"]:
        report.add_check(CheckResult(
            name="RMS Level",
            severity=Severity.PASS,
            message=f"RMS level OK: {rms_db:.1f} dB",
            actual_value=round(rms_db, 1),
            expected_value=f"{ACX_SPECS['rms_min_db']} to {ACX_SPECS['rms_max_db']} dB",
        ))
    elif rms_db < ACX_SPECS["rms_min_db"]:
        report.add_check(CheckResult(
            name="RMS Level",
            severity=Severity.FAIL,
            message=f"RMS too quiet: {rms_db:.1f} dB (minimum {ACX_SPECS['rms_min_db']} dB)",
            actual_value=round(rms_db, 1),
            expected_value=f"{ACX_SPECS['rms_min_db']} to {ACX_SPECS['rms_max_db']} dB",
        ))
    else:
        report.add_check(CheckResult(
            name="RMS Level",
            severity=Severity.FAIL,
            message=f"RMS too loud: {rms_db:.1f} dB (maximum {ACX_SPECS['rms_max_db']} dB)",
            actual_value=round(rms_db, 1),
            expected_value=f"{ACX_SPECS['rms_min_db']} to {ACX_SPECS['rms_max_db']} dB",
        ))

    # LUFS Level (ITU-R BS.1770 — broadcast standard, more accurate than RMS)
    lufs = calculate_lufs(samples, sr)
    if lufs is not None:
        report.metadata["lufs"] = round(lufs, 2)
        if ACX_SPECS["rms_min_db"] <= lufs <= ACX_SPECS["rms_max_db"]:
            report.add_check(CheckResult(
                name="Integrated Loudness (LUFS)",
                severity=Severity.PASS,
                message=f"LUFS level OK: {lufs:.1f} LUFS",
                actual_value=round(lufs, 1),
                expected_value=f"{ACX_SPECS['rms_min_db']} to {ACX_SPECS['rms_max_db']} LUFS",
            ))
        elif lufs < ACX_SPECS["rms_min_db"]:
            report.add_check(CheckResult(
                name="Integrated Loudness (LUFS)",
                severity=Severity.FAIL,
                message=f"LUFS too quiet: {lufs:.1f} LUFS (minimum {ACX_SPECS['rms_min_db']} LUFS)",
                actual_value=round(lufs, 1),
                expected_value=f"{ACX_SPECS['rms_min_db']} to {ACX_SPECS['rms_max_db']} LUFS",
            ))
        else:
            report.add_check(CheckResult(
                name="Integrated Loudness (LUFS)",
                severity=Severity.FAIL,
                message=f"LUFS too loud: {lufs:.1f} LUFS (maximum {ACX_SPECS['rms_max_db']} LUFS)",
                actual_value=round(lufs, 1),
                expected_value=f"{ACX_SPECS['rms_min_db']} to {ACX_SPECS['rms_max_db']} LUFS",
            ))

    # Peak Level
    peak_db = calculate_peak_db(samples)
    report.metadata["peak_db"] = round(peak_db, 2)

    if peak_db <= ACX_SPECS["peak_max_db"]:
        report.add_check(CheckResult(
            name="Peak Level",
            severity=Severity.PASS,
            message=f"Peak level OK: {peak_db:.1f} dB",
            actual_value=round(peak_db, 1),
            expected_value=f"<= {ACX_SPECS['peak_max_db']} dB",
        ))
    else:
        report.add_check(CheckResult(
            name="Peak Level",
            severity=Severity.FAIL,
            message=f"Peak too high: {peak_db:.1f} dB (maximum {ACX_SPECS['peak_max_db']} dB)",
            actual_value=round(peak_db, 1),
            expected_value=f"<= {ACX_SPECS['peak_max_db']} dB",
        ))

    # Noise Floor
    noise_floor_db = calculate_noise_floor_db(samples, sr)
    report.metadata["noise_floor_db"] = round(noise_floor_db, 2)

    if noise_floor_db <= ACX_SPECS["noise_floor_max_db"]:
        report.add_check(CheckResult(
            name="Noise Floor",
            severity=Severity.PASS,
            message=f"Noise floor OK: {noise_floor_db:.1f} dB",
            actual_value=round(noise_floor_db, 1),
            expected_value=f"<= {ACX_SPECS['noise_floor_max_db']} dB",
        ))
    else:
        report.add_check(CheckResult(
            name="Noise Floor",
            severity=Severity.FAIL,
            message=f"Noise floor too high: {noise_floor_db:.1f} dB (maximum {ACX_SPECS['noise_floor_max_db']} dB)",
            actual_value=round(noise_floor_db, 1),
            expected_value=f"<= {ACX_SPECS['noise_floor_max_db']} dB",
        ))

    # === ROOM TONE CHECKS ===

    start_silence, end_silence = check_room_tone(samples, sr)
    report.metadata["room_tone_start_sec"] = round(start_silence, 2)
    report.metadata["room_tone_end_sec"] = round(end_silence, 2)

    # Start room tone
    if ACX_SPECS["room_tone_start_min_sec"] <= start_silence <= ACX_SPECS["room_tone_start_max_sec"]:
        report.add_check(CheckResult(
            name="Room Tone (Start)",
            severity=Severity.PASS,
            message=f"Start room tone OK: {start_silence:.2f} sec",
            actual_value=round(start_silence, 2),
            expected_value=f"{ACX_SPECS['room_tone_start_min_sec']}-{ACX_SPECS['room_tone_start_max_sec']} sec",
        ))
    elif start_silence < ACX_SPECS["room_tone_start_min_sec"]:
        severity = Severity.FAIL if strict else Severity.WARNING
        report.add_check(CheckResult(
            name="Room Tone (Start)",
            severity=severity,
            message=f"Start room tone too short: {start_silence:.2f} sec",
            actual_value=round(start_silence, 2),
            expected_value=f"{ACX_SPECS['room_tone_start_min_sec']}-{ACX_SPECS['room_tone_start_max_sec']} sec",
        ))
    else:
        severity = Severity.FAIL if strict else Severity.WARNING
        report.add_check(CheckResult(
            name="Room Tone (Start)",
            severity=severity,
            message=f"Start room tone too long: {start_silence:.2f} sec",
            actual_value=round(start_silence, 2),
            expected_value=f"{ACX_SPECS['room_tone_start_min_sec']}-{ACX_SPECS['room_tone_start_max_sec']} sec",
        ))

    # End room tone
    if end_silence <= ACX_SPECS["room_tone_end_max_sec"]:
        report.add_check(CheckResult(
            name="Room Tone (End)",
            severity=Severity.PASS,
            message=f"End room tone OK: {end_silence:.2f} sec",
            actual_value=round(end_silence, 2),
            expected_value=f"<= {ACX_SPECS['room_tone_end_max_sec']} sec",
        ))
    else:
        severity = Severity.FAIL if strict else Severity.WARNING
        report.add_check(CheckResult(
            name="Room Tone (End)",
            severity=severity,
            message=f"End room tone too long: {end_silence:.2f} sec",
            actual_value=round(end_silence, 2),
            expected_value=f"<= {ACX_SPECS['room_tone_end_max_sec']} sec",
        ))

    # Duration check (sanity)
    duration = metadata.get("duration_seconds", 0)
    if duration > 120 * 60:  # 120 minutes
        report.add_check(CheckResult(
            name="Duration",
            severity=Severity.FAIL,
            message=f"File too long: {duration/60:.1f} minutes (maximum 120 minutes)",
            actual_value=round(duration/60, 1),
            expected_value="<= 120 minutes",
        ))
    else:
        report.add_check(CheckResult(
            name="Duration",
            severity=Severity.PASS,
            message=f"Duration OK: {duration/60:.1f} minutes",
            actual_value=round(duration/60, 1),
            expected_value="<= 120 minutes",
        ))

    return report


def validate_directory(dir_path: str, strict: bool = False) -> List[ValidationReport]:
    """Validate all audio files in a directory."""
    reports = []
    audio_extensions = {'.mp3', '.wav', '.flac'}

    for file_path in sorted(Path(dir_path).rglob('*')):
        if file_path.suffix.lower() in audio_extensions:
            reports.append(validate_audio(str(file_path), strict))

    return reports


def main():
    parser = argparse.ArgumentParser(
        description="Validate audio files against ACX/Audible specifications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("path", help="Audio file or directory to validate")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    parser.add_argument("--quiet", "-q", action="store_true", help="Only output failures")

    args = parser.parse_args()

    path = Path(args.path)

    if path.is_dir():
        reports = validate_directory(str(path), args.strict)
    elif path.is_file():
        reports = [validate_audio(str(path), args.strict)]
    else:
        print(f"Error: Path not found: {args.path}", file=sys.stderr)
        sys.exit(1)

    if not reports:
        print("No audio files found.", file=sys.stderr)
        sys.exit(1)

    # Output results
    if args.json:
        output = {
            "reports": [r.to_dict() for r in reports],
            "summary": {
                "total": len(reports),
                "passed": sum(1 for r in reports if r.passed),
                "failed": sum(1 for r in reports if not r.passed),
            }
        }
        print(json.dumps(output, indent=2))
    else:
        for report in reports:
            if args.quiet and report.passed:
                continue
            print(report.summary())

        # Summary for multiple files
        if len(reports) > 1:
            passed = sum(1 for r in reports if r.passed)
            print(f"\n{'='*60}")
            print(f"SUMMARY: {passed}/{len(reports)} files passed")
            print("="*60)

    # Exit code
    all_passed = all(r.passed for r in reports)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
