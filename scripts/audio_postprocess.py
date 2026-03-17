#!/usr/bin/env python3
"""
Audio post-processing for ACX compliance.

Mastering chain:
1. High-pass filter at 80 Hz (remove rumble)
2. Low-pass filter at 16 kHz (remove hiss)
3. Gentle compression (2.5:1 ratio, -24 dB threshold)
4. De-essing (4-8 kHz sibilance reduction)
5. Limiter (-3 dB ceiling)
6. Loudness normalization to -20 dB RMS
7. Room tone insertion (0.5s head, 3s tail)
8. Export: 192 kbps CBR MP3, 44.1 kHz, mono

Design principles:
- Gentle processing (ACX human QC rejects over-processed audio)
- Deterministic output (same input = identical output)
- Preserve natural dynamics and breath sounds

Usage:
    # Process single file
    python audio_postprocess.py input.wav --output output.mp3

    # Process directory
    python audio_postprocess.py input_dir/ --output-dir output_dir/

    # Preview without writing (analyze only)
    python audio_postprocess.py input.wav --analyze

    # Custom parameters
    python audio_postprocess.py input.wav --output output.mp3 \
        --target-rms -20 --limiter-ceiling -3 --room-tone-head 0.5 --room-tone-tail 3.0
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Tuple, List
import numpy as np

# Optional high-quality backends (graceful fallback to pure-Python)
try:
    import pyloudnorm as pyln
    PYLOUDNORM_AVAILABLE = True
except ImportError:
    PYLOUDNORM_AVAILABLE = False

try:
    import pedalboard
    PEDALBOARD_AVAILABLE = True
except ImportError:
    PEDALBOARD_AVAILABLE = False

# Target sample rate for ACX
TARGET_SAMPLE_RATE = 44100
TARGET_BIT_RATE = 192  # kbps


@dataclass
class ProcessingParams:
    """Parameters for the mastering chain."""
    # Filters
    highpass_freq: float = 80.0  # Hz
    lowpass_freq: float = 16000.0  # Hz
    filter_order: int = 4  # Butterworth order (24 dB/octave)

    # Compression
    comp_threshold_db: float = -24.0
    comp_ratio: float = 2.5
    comp_attack_ms: float = 10.0
    comp_release_ms: float = 100.0
    comp_knee_db: float = 6.0  # Soft knee

    # De-esser
    deess_freq_low: float = 4000.0  # Hz
    deess_freq_high: float = 8000.0  # Hz
    deess_threshold_db: float = -20.0
    deess_ratio: float = 4.0
    deess_attack_ms: float = 0.5
    deess_release_ms: float = 50.0

    # Limiter
    limiter_ceiling_db: float = -3.0
    limiter_release_ms: float = 50.0

    # Normalization
    target_rms_db: float = -20.0  # Center of ACX range (-23 to -18)

    # Room tone
    room_tone_head_sec: float = 0.5
    room_tone_tail_sec: float = 3.0
    room_tone_level_db: float = -70.0  # Very quiet noise floor

    def to_dict(self) -> dict:
        return asdict(self)


# --- Content-type presets ---
# Auto-detected by batch_produce.py from manuscript analysis.

CONTENT_PRESETS = {
    "childrens": ProcessingParams(
        # Bright, clear, wide dynamic range for expressive reading
        comp_threshold_db=-20.0,
        comp_ratio=2.0,
        target_rms_db=-20.0,
        room_tone_head_sec=0.5,
        room_tone_tail_sec=3.0,
    ),
    "literary": ProcessingParams(
        # Preserve dynamics and breath — minimal processing
        comp_threshold_db=-26.0,
        comp_ratio=2.0,
        target_rms_db=-20.0,
        room_tone_head_sec=0.5,
        room_tone_tail_sec=3.0,
    ),
    "thriller": ProcessingParams(
        # Tighter compression for consistent intensity, no whisper drop-off
        comp_threshold_db=-22.0,
        comp_ratio=3.0,
        comp_attack_ms=5.0,
        target_rms_db=-19.0,
        limiter_ceiling_db=-3.0,
        room_tone_head_sec=0.5,
        room_tone_tail_sec=3.0,
    ),
    "nonfiction": ProcessingParams(
        # Even, lecture-like levels — heavier compression for consistency
        comp_threshold_db=-22.0,
        comp_ratio=3.5,
        comp_attack_ms=8.0,
        target_rms_db=-19.0,
        room_tone_head_sec=0.5,
        room_tone_tail_sec=3.0,
    ),
}


def detect_content_type(text: str) -> str:
    """
    Auto-detect content type from manuscript text for mastering preset selection.

    Heuristics:
    - Children's: short (< 2000 words), [PAGE TURN] markers, simple vocabulary
    - Thriller: dark vocabulary, short sentences, high dialogue ratio
    - Nonfiction: long paragraphs, low dialogue, formal language
    - Literary: default fallback (gentle processing)
    """
    words = text.split()
    word_count = len(words)

    # Children's: short + page turns
    if word_count < 2000 and "[PAGE TURN]" in text:
        return "childrens"
    if word_count < 1500:
        return "childrens"

    # Count dialogue lines vs total
    lines = [ln.strip() for ln in text.split('\n') if ln.strip()]
    dialogue_lines = sum(
        1 for ln in lines if ln.startswith('"') or ln.startswith('\u201c')
    )
    dialogue_ratio = dialogue_lines / max(len(lines), 1)

    # Thriller signals
    thriller_words = {
        'blood', 'gun', 'knife', 'murder', 'death', 'scream', 'shadow',
        'darkness', 'killer', 'chase', 'fear', 'threat', 'danger', 'weapon',
        'escape', 'detective', 'suspect', 'crime', 'victim', 'terror',
    }
    text_lower = text.lower()
    thriller_hits = sum(1 for w in thriller_words if w in text_lower)
    if thriller_hits >= 5 and dialogue_ratio > 0.2:
        return "thriller"

    # Nonfiction signals: low dialogue, long paragraphs
    if dialogue_ratio < 0.05:
        paragraphs = text.split('\n\n')
        avg_para_len = sum(len(p.split()) for p in paragraphs) / max(len(paragraphs), 1)
        if avg_para_len > 80:
            return "nonfiction"

    return "literary"


def get_content_params(content_type: str) -> ProcessingParams:
    """Get mastering params for a content type. Falls back to default."""
    return CONTENT_PRESETS.get(content_type, ProcessingParams())


def load_audio(file_path: str) -> Tuple[np.ndarray, int]:
    """Load audio file and return samples + sample rate."""
    try:
        import soundfile as sf
    except ImportError:
        raise ImportError("Install soundfile: pip install soundfile")

    samples, sr = sf.read(file_path, dtype='float64')

    # Convert stereo to mono
    if len(samples.shape) > 1:
        samples = np.mean(samples, axis=1)

    return samples, sr


def save_audio_wav(samples: np.ndarray, sample_rate: int, file_path: str):
    """Save audio to WAV file."""
    try:
        import soundfile as sf
    except ImportError:
        raise ImportError("Install soundfile: pip install soundfile")

    # Ensure directory exists
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    sf.write(file_path, samples, sample_rate, subtype='PCM_16')


def save_audio_mp3(samples: np.ndarray, sample_rate: int, file_path: str, bitrate: int = 192):
    """Save audio to MP3 file using pydub."""
    try:
        from pydub import AudioSegment
    except ImportError:
        raise ImportError("Install pydub: pip install pydub")

    # Ensure directory exists
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    # Convert to 16-bit PCM
    samples_16bit = np.clip(samples * 32767, -32768, 32767).astype(np.int16)

    # Create AudioSegment
    audio = AudioSegment(
        samples_16bit.tobytes(),
        frame_rate=sample_rate,
        sample_width=2,  # 16-bit = 2 bytes
        channels=1,
    )

    # Export as CBR MP3
    audio.export(
        file_path,
        format="mp3",
        bitrate=f"{bitrate}k",
        parameters=["-ar", str(sample_rate)],  # Ensure correct sample rate
    )


def resample(samples: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    """Resample audio to target sample rate."""
    if orig_sr == target_sr:
        return samples

    try:
        from scipy import signal
    except ImportError:
        raise ImportError("Install scipy: pip install scipy")

    # Calculate resampling ratio
    num_samples = int(len(samples) * target_sr / orig_sr)
    return signal.resample(samples, num_samples)


def apply_highpass(samples: np.ndarray, sample_rate: int, cutoff: float, order: int = 4) -> np.ndarray:
    """Apply high-pass Butterworth filter."""
    try:
        from scipy.signal import butter, sosfilt
    except ImportError:
        raise ImportError("Install scipy: pip install scipy")

    nyquist = sample_rate / 2
    normalized_cutoff = cutoff / nyquist

    # Use second-order sections for numerical stability
    sos = butter(order, normalized_cutoff, btype='high', output='sos')
    return sosfilt(sos, samples)


def apply_lowpass(samples: np.ndarray, sample_rate: int, cutoff: float, order: int = 4) -> np.ndarray:
    """Apply low-pass Butterworth filter."""
    try:
        from scipy.signal import butter, sosfilt
    except ImportError:
        raise ImportError("Install scipy: pip install scipy")

    nyquist = sample_rate / 2
    normalized_cutoff = min(cutoff / nyquist, 0.99)  # Must be < 1

    sos = butter(order, normalized_cutoff, btype='low', output='sos')
    return sosfilt(sos, samples)


def apply_compression(
    samples: np.ndarray,
    sample_rate: int,
    threshold_db: float,
    ratio: float,
    attack_ms: float,
    release_ms: float,
    knee_db: float = 0.0,
) -> np.ndarray:
    """
    Apply dynamic range compression with soft knee.

    Uses envelope follower for smooth gain reduction.
    """
    # Convert parameters
    threshold = 10 ** (threshold_db / 20)
    attack_coef = np.exp(-1.0 / (attack_ms * sample_rate / 1000))
    release_coef = np.exp(-1.0 / (release_ms * sample_rate / 1000))
    knee_width = 10 ** (knee_db / 20) if knee_db > 0 else 0

    # Envelope follower
    envelope = np.zeros_like(samples)
    env = 0.0

    for i, sample in enumerate(np.abs(samples)):
        if sample > env:
            env = attack_coef * env + (1 - attack_coef) * sample
        else:
            env = release_coef * env + (1 - release_coef) * sample
        envelope[i] = env

    # Calculate gain reduction
    output = np.copy(samples)

    for i, env in enumerate(envelope):
        if env <= 0:
            continue

        # Soft knee calculation
        if knee_width > 0 and env > threshold - knee_width and env < threshold + knee_width:
            # In knee region - gradual compression
            knee_factor = (env - threshold + knee_width) / (2 * knee_width)
            effective_ratio = 1 + (ratio - 1) * knee_factor
            gain_db = (1 - 1/effective_ratio) * (20 * np.log10(env / threshold))
        elif env > threshold:
            # Above threshold - full compression
            over_db = 20 * np.log10(env / threshold)
            gain_db = over_db * (1 - 1/ratio)
        else:
            gain_db = 0

        gain = 10 ** (-gain_db / 20)
        output[i] = samples[i] * gain

    return output


def apply_deesser(
    samples: np.ndarray,
    sample_rate: int,
    freq_low: float,
    freq_high: float,
    threshold_db: float,
    ratio: float,
    attack_ms: float,
    release_ms: float,
) -> np.ndarray:
    """
    Apply de-essing by compressing the sibilant frequency band.

    Uses bandpass filter to isolate sibilance, then applies
    frequency-selective compression.
    """
    try:
        from scipy.signal import butter, sosfilt
    except ImportError:
        raise ImportError("Install scipy: pip install scipy")

    nyquist = sample_rate / 2
    low = freq_low / nyquist
    high = min(freq_high / nyquist, 0.99)

    # Bandpass filter to isolate sibilance
    sos = butter(2, [low, high], btype='band', output='sos')
    sibilant = sosfilt(sos, samples)

    # Calculate sibilance envelope
    threshold = 10 ** (threshold_db / 20)
    attack_coef = np.exp(-1.0 / (attack_ms * sample_rate / 1000))
    release_coef = np.exp(-1.0 / (release_ms * sample_rate / 1000))

    envelope = np.zeros_like(sibilant)
    env = 0.0

    for i, sample in enumerate(np.abs(sibilant)):
        if sample > env:
            env = attack_coef * env + (1 - attack_coef) * sample
        else:
            env = release_coef * env + (1 - release_coef) * sample
        envelope[i] = env

    # Apply frequency-selective gain reduction
    output = np.copy(samples)

    for i, env in enumerate(envelope):
        if env > threshold:
            over_db = 20 * np.log10(env / threshold)
            gain_reduction_db = over_db * (1 - 1/ratio)
            gain = 10 ** (-gain_reduction_db / 20)

            # Apply reduction only to sibilant component
            output[i] = samples[i] - sibilant[i] * (1 - gain)

    return output


def apply_limiter(
    samples: np.ndarray,
    sample_rate: int,
    ceiling_db: float,
    release_ms: float = 50.0,
) -> np.ndarray:
    """
    Apply brick-wall limiter with lookahead.

    Uses 5ms lookahead for transparent limiting.
    """
    ceiling = 10 ** (ceiling_db / 20)
    lookahead_samples = int(5 * sample_rate / 1000)  # 5ms lookahead
    release_coef = np.exp(-1.0 / (release_ms * sample_rate / 1000))

    # Pad for lookahead
    padded = np.concatenate([samples, np.zeros(lookahead_samples)])
    output = np.zeros_like(padded)

    gain = 1.0

    for i in range(len(samples)):
        # Look ahead for peaks
        lookahead_peak = np.max(np.abs(padded[i:i + lookahead_samples]))

        # Calculate required gain reduction
        if lookahead_peak > ceiling:
            target_gain = ceiling / lookahead_peak
        else:
            target_gain = 1.0

        # Smooth gain changes
        if target_gain < gain:
            gain = target_gain  # Instant attack
        else:
            gain = release_coef * gain + (1 - release_coef) * target_gain

        output[i] = samples[i] * gain

    return output[:len(samples)]


def calculate_rms(samples: np.ndarray) -> float:
    """Calculate RMS level."""
    return np.sqrt(np.mean(samples ** 2))


def calculate_rms_db(samples: np.ndarray) -> float:
    """Calculate RMS level in dB."""
    rms = calculate_rms(samples)
    if rms > 0:
        return 20 * np.log10(rms)
    return -100.0


def calculate_lufs(samples: np.ndarray, sample_rate: int) -> float:
    """
    Calculate integrated loudness in LUFS (ITU-R BS.1770-4).

    LUFS is the broadcast standard for loudness measurement, using
    perceptual K-weighting and gated integration. More accurate than
    simple RMS for human-perceived loudness.

    Falls back to RMS if pyloudnorm is not installed.
    """
    if PYLOUDNORM_AVAILABLE:
        meter = pyln.Meter(sample_rate)
        return meter.integrated_loudness(samples)
    else:
        # Fallback: approximate LUFS as RMS dB (not perceptually weighted)
        return calculate_rms_db(samples)


def normalize_loudness(samples: np.ndarray, target_rms_db: float, sample_rate: int = TARGET_SAMPLE_RATE) -> np.ndarray:
    """
    Normalize to target loudness level.

    When pyloudnorm is available, uses ITU-R BS.1770-4 integrated LUFS
    measurement with K-weighting — the broadcast standard that ACX and
    all major platforms actually measure against.

    Falls back to simple RMS normalization otherwise.
    """
    if PYLOUDNORM_AVAILABLE:
        meter = pyln.Meter(sample_rate)
        current_lufs = meter.integrated_loudness(samples)
        return pyln.normalize.loudness(samples, current_lufs, target_rms_db)
    else:
        current_rms_db = calculate_rms_db(samples)
        gain_db = target_rms_db - current_rms_db
        gain = 10 ** (gain_db / 20)
        return samples * gain


def generate_room_tone(duration_sec: float, sample_rate: int, level_db: float = -70.0) -> np.ndarray:
    """
    Generate room tone (very quiet noise).

    Uses pink noise filtered to sound natural.
    """
    num_samples = int(duration_sec * sample_rate)

    # Generate white noise
    rng = np.random.default_rng(42)  # Local RNG — does not affect global state
    white_noise = rng.standard_normal(num_samples)

    # Convert to pink noise (1/f spectrum) using simple filtering
    # This is a simplified approach - applies gentle lowpass
    try:
        from scipy.signal import butter, sosfilt
        sos = butter(1, 1000 / (sample_rate / 2), btype='low', output='sos')
        pink_noise = sosfilt(sos, white_noise)
    except ImportError:
        # Fallback to white noise if scipy not available
        pink_noise = white_noise

    # Scale to target level
    target_amplitude = 10 ** (level_db / 20)
    current_rms = np.sqrt(np.mean(pink_noise ** 2))
    if current_rms > 0:
        pink_noise = pink_noise * (target_amplitude / current_rms)

    return pink_noise


def add_room_tone(
    samples: np.ndarray,
    sample_rate: int,
    head_sec: float,
    tail_sec: float,
    level_db: float = -70.0,
) -> np.ndarray:
    """Add room tone at head and tail of audio."""
    head = generate_room_tone(head_sec, sample_rate, level_db)
    tail = generate_room_tone(tail_sec, sample_rate, level_db)

    # Short crossfade for smooth transition (10ms)
    fade_samples = int(0.01 * sample_rate)

    if fade_samples > 0 and len(samples) > fade_samples:
        # Fade in at start
        fade_in = np.linspace(0, 1, fade_samples)
        samples[:fade_samples] = samples[:fade_samples] * fade_in

        # Fade out at end
        fade_out = np.linspace(1, 0, fade_samples)
        samples[-fade_samples:] = samples[-fade_samples:] * fade_out

    return np.concatenate([head, samples, tail])


def process_audio(
    samples: np.ndarray,
    sample_rate: int,
    params: ProcessingParams,
    verbose: bool = False,
) -> np.ndarray:
    """
    Apply full mastering chain.

    Order matters:
    1. Resample to 44.1 kHz (if needed)
    2. High-pass filter (remove rumble)
    3. Low-pass filter (remove hiss)
    4. Compression (even out dynamics)
    5. De-essing (reduce sibilance)
    6. Limiter (prevent clipping)
    7. Loudness normalization (hit target RMS)
    8. Room tone (ACX requirement)
    """
    # 1. Resample if needed
    if sample_rate != TARGET_SAMPLE_RATE:
        if verbose:
            print(f"  Resampling: {sample_rate} Hz → {TARGET_SAMPLE_RATE} Hz")
        samples = resample(samples, sample_rate, TARGET_SAMPLE_RATE)
        sample_rate = TARGET_SAMPLE_RATE

    # 2. High-pass filter
    if verbose:
        print(f"  High-pass filter: {params.highpass_freq} Hz")
    samples = apply_highpass(samples, sample_rate, params.highpass_freq, params.filter_order)

    # 3. Low-pass filter
    if verbose:
        print(f"  Low-pass filter: {params.lowpass_freq} Hz")
    samples = apply_lowpass(samples, sample_rate, params.lowpass_freq, params.filter_order)

    # 4. Compression
    if verbose:
        rms_before = calculate_rms_db(samples)
        print(f"  Compression: {params.comp_ratio}:1 @ {params.comp_threshold_db} dB")
    samples = apply_compression(
        samples, sample_rate,
        params.comp_threshold_db,
        params.comp_ratio,
        params.comp_attack_ms,
        params.comp_release_ms,
        params.comp_knee_db,
    )
    if verbose:
        rms_after = calculate_rms_db(samples)
        print(f"    RMS: {rms_before:.1f} → {rms_after:.1f} dB")

    # 5. De-essing
    if verbose:
        print(f"  De-esser: {params.deess_freq_low}-{params.deess_freq_high} Hz")
    samples = apply_deesser(
        samples, sample_rate,
        params.deess_freq_low,
        params.deess_freq_high,
        params.deess_threshold_db,
        params.deess_ratio,
        params.deess_attack_ms,
        params.deess_release_ms,
    )

    # 6. Limiter
    if verbose:
        print(f"  Limiter: ceiling {params.limiter_ceiling_db} dB")
    samples = apply_limiter(samples, sample_rate, params.limiter_ceiling_db, params.limiter_release_ms)

    # 7. Loudness normalization (LUFS when pyloudnorm available, RMS fallback)
    if verbose:
        rms_before = calculate_rms_db(samples)
        method = "LUFS (ITU-R BS.1770)" if PYLOUDNORM_AVAILABLE else "RMS"
        print(f"  Normalize: target {params.target_rms_db} dB ({method})")
    samples = normalize_loudness(samples, params.target_rms_db, sample_rate)
    if verbose:
        rms_after = calculate_rms_db(samples)
        print(f"    RMS: {rms_before:.1f} → {rms_after:.1f} dB")
        if PYLOUDNORM_AVAILABLE:
            lufs = calculate_lufs(samples, sample_rate)
            print(f"    LUFS: {lufs:.1f}")

    # 8. Room tone
    if verbose:
        print(f"  Room tone: {params.room_tone_head_sec}s head, {params.room_tone_tail_sec}s tail")
    samples = add_room_tone(
        samples, sample_rate,
        params.room_tone_head_sec,
        params.room_tone_tail_sec,
        params.room_tone_level_db,
    )

    return samples


def process_audio_pedalboard(
    samples: np.ndarray,
    sample_rate: int,
    params: ProcessingParams,
    verbose: bool = False,
) -> np.ndarray:
    """
    Pedalboard-accelerated mastering chain (Spotify's C++ audio DSP).

    ~100x faster than pure-Python sample-by-sample processing.
    Same signal chain as process_audio() but using studio-quality
    C++ implementations via pedalboard.

    Requires: pip install pedalboard pyloudnorm
    """
    if not PEDALBOARD_AVAILABLE:
        raise ImportError("pedalboard not installed: pip install pedalboard")

    from pedalboard import (
        Pedalboard, Compressor, HighpassFilter, LowpassFilter,
        Limiter, Gain,
    )

    if verbose:
        print("  [pedalboard] Using Spotify C++ DSP backend")

    # 1. Resample if needed
    if sample_rate != TARGET_SAMPLE_RATE:
        if verbose:
            print(f"  Resampling: {sample_rate} Hz → {TARGET_SAMPLE_RATE} Hz")
        samples = resample(samples, sample_rate, TARGET_SAMPLE_RATE)
        sample_rate = TARGET_SAMPLE_RATE

    # Build the effects chain
    board = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=params.highpass_freq),
        LowpassFilter(cutoff_frequency_hz=params.lowpass_freq),
        Compressor(
            threshold_db=params.comp_threshold_db,
            ratio=params.comp_ratio,
            attack_ms=params.comp_attack_ms,
            release_ms=params.comp_release_ms,
        ),
        # De-essing: pedalboard doesn't have a dedicated de-esser,
        # so we fall back to the pure-Python implementation for this stage
        Limiter(
            threshold_db=params.limiter_ceiling_db,
            release_ms=params.limiter_release_ms,
        ),
    ])

    if verbose:
        print(f"  [pedalboard] Chain: HPF({params.highpass_freq}Hz) → "
              f"LPF({params.lowpass_freq}Hz) → "
              f"Comp({params.comp_ratio}:1 @ {params.comp_threshold_db}dB) → "
              f"Limiter({params.limiter_ceiling_db}dB)")

    # Pedalboard expects shape (channels, samples) as float32
    audio_2d = samples.astype(np.float32).reshape(1, -1)
    processed = board(audio_2d, sample_rate)
    samples = processed.flatten().astype(np.float64)

    # De-essing (pure-Python — pedalboard lacks dedicated de-esser)
    if verbose:
        print(f"  De-esser: {params.deess_freq_low}-{params.deess_freq_high} Hz")
    samples = apply_deesser(
        samples, sample_rate,
        params.deess_freq_low, params.deess_freq_high,
        params.deess_threshold_db, params.deess_ratio,
        params.deess_attack_ms, params.deess_release_ms,
    )

    # LUFS normalization
    method = "LUFS (ITU-R BS.1770)" if PYLOUDNORM_AVAILABLE else "RMS"
    if verbose:
        print(f"  Normalize: target {params.target_rms_db} dB ({method})")
    samples = normalize_loudness(samples, params.target_rms_db, sample_rate)

    if verbose and PYLOUDNORM_AVAILABLE:
        lufs = calculate_lufs(samples, sample_rate)
        print(f"    LUFS: {lufs:.1f}")

    # Room tone
    if verbose:
        print(f"  Room tone: {params.room_tone_head_sec}s head, {params.room_tone_tail_sec}s tail")
    samples = add_room_tone(
        samples, sample_rate,
        params.room_tone_head_sec, params.room_tone_tail_sec,
        params.room_tone_level_db,
    )

    return samples


def analyze_audio(file_path: str) -> dict:
    """Analyze audio file and return metrics including LUFS when available."""
    samples, sr = load_audio(file_path)

    peak = np.max(np.abs(samples))
    peak_db = 20 * np.log10(peak) if peak > 0 else -100

    rms = calculate_rms(samples)
    rms_db = 20 * np.log10(rms) if rms > 0 else -100

    duration = len(samples) / sr

    result = {
        "file": file_path,
        "duration_sec": round(duration, 2),
        "sample_rate": sr,
        "peak_db": round(peak_db, 2),
        "rms_db": round(rms_db, 2),
        "acx_rms_pass": -23 <= rms_db <= -18,
        "acx_peak_pass": peak_db <= -3,
    }

    # Add LUFS measurement when pyloudnorm is available
    if PYLOUDNORM_AVAILABLE:
        lufs = calculate_lufs(samples, sr)
        result["lufs"] = round(lufs, 2)
        # ACX range in LUFS is approximately -23 to -18
        result["acx_lufs_pass"] = -23 <= lufs <= -18

    return result


def process_file(
    input_path: str,
    output_path: str,
    params: ProcessingParams,
    verbose: bool = False,
) -> dict:
    """Process a single audio file."""
    if verbose:
        print(f"\nProcessing: {input_path}")

    # Load
    samples, sr = load_audio(input_path)
    if verbose:
        print(f"  Input: {sr} Hz, {len(samples)/sr:.1f}s, RMS {calculate_rms_db(samples):.1f} dB")
        if PYLOUDNORM_AVAILABLE:
            lufs = calculate_lufs(samples, sr)
            print(f"  Input LUFS: {lufs:.1f}")

    # Process — use pedalboard C++ backend when available for ~100x speedup
    if PEDALBOARD_AVAILABLE:
        processed = process_audio_pedalboard(samples, sr, params, verbose)
    else:
        processed = process_audio(samples, sr, params, verbose)

    # Save
    ext = Path(output_path).suffix.lower()
    if ext == '.mp3':
        save_audio_mp3(processed, TARGET_SAMPLE_RATE, output_path, TARGET_BIT_RATE)
    else:
        save_audio_wav(processed, TARGET_SAMPLE_RATE, output_path)

    if verbose:
        print(f"  Output: {output_path}")

    # Return analysis of output
    return analyze_audio(output_path)


def process_directory(
    input_dir: str,
    output_dir: str,
    params: ProcessingParams,
    verbose: bool = False,
) -> List[dict]:
    """Process all audio files in a directory."""
    results = []
    audio_extensions = {'.wav', '.mp3', '.flac', '.ogg'}

    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for file_path in sorted(input_path.glob('*')):
        if file_path.suffix.lower() in audio_extensions:
            # Output as MP3
            out_file = output_path / (file_path.stem + '.mp3')
            result = process_file(str(file_path), str(out_file), params, verbose)
            results.append(result)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Post-process audio for ACX compliance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("input", help="Input audio file or directory")
    parser.add_argument("--output", "-o", help="Output file or directory")
    parser.add_argument("--output-dir", help="Output directory (for batch processing)")

    # Analysis mode
    parser.add_argument("--analyze", action="store_true",
                        help="Analyze input without processing")

    # Processing parameters
    parser.add_argument("--target-rms", type=float, default=-20.0,
                        help="Target RMS level in dB (default: -20)")
    parser.add_argument("--limiter-ceiling", type=float, default=-3.0,
                        help="Limiter ceiling in dB (default: -3)")
    parser.add_argument("--room-tone-head", type=float, default=0.5,
                        help="Room tone at head in seconds (default: 0.5)")
    parser.add_argument("--room-tone-tail", type=float, default=3.0,
                        help="Room tone at tail in seconds (default: 3.0)")

    # Output options
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose output")
    parser.add_argument("--json", action="store_true",
                        help="Output results as JSON")

    args = parser.parse_args()

    # Build parameters
    params = ProcessingParams(
        target_rms_db=args.target_rms,
        limiter_ceiling_db=args.limiter_ceiling,
        room_tone_head_sec=args.room_tone_head,
        room_tone_tail_sec=args.room_tone_tail,
    )

    input_path = Path(args.input)

    # Analysis mode
    if args.analyze:
        if input_path.is_file():
            result = analyze_audio(str(input_path))
        else:
            result = [analyze_audio(str(f)) for f in sorted(input_path.glob('*'))
                      if f.suffix.lower() in {'.wav', '.mp3', '.flac'}]

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if isinstance(result, list):
                for r in result:
                    print(f"{r['file']}: RMS={r['rms_db']:.1f}dB, Peak={r['peak_db']:.1f}dB")
            else:
                print(f"Duration: {result['duration_sec']}s")
                print(f"Sample rate: {result['sample_rate']} Hz")
                print(f"RMS: {result['rms_db']:.1f} dB {'PASS' if result['acx_rms_pass'] else 'FAIL'}")
                print(f"Peak: {result['peak_db']:.1f} dB {'PASS' if result['acx_peak_pass'] else 'FAIL'}")
        return

    # Processing mode
    if input_path.is_dir():
        output_dir = args.output_dir or args.output
        if not output_dir:
            print("Error: --output-dir required for directory input", file=sys.stderr)
            sys.exit(1)
        results = process_directory(str(input_path), output_dir, params, args.verbose)
    else:
        output = args.output
        if not output:
            # Default: same name with _processed suffix
            output = str(input_path.stem) + "_processed.mp3"
        results = [process_file(str(input_path), output, params, args.verbose)]

    # Output results
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        passed = sum(1 for r in results if r['acx_rms_pass'] and r['acx_peak_pass'])
        print(f"\nProcessed {len(results)} file(s), {passed} ACX-compliant")


if __name__ == "__main__":
    main()
