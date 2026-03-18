"""Pytest configuration and shared test fixtures."""

import os
import sys
import tempfile
from pathlib import Path

# __file__ is scripts/tests/conftest.py → parent.parent is scripts/
sys.path.insert(0, str(Path(__file__).parent.parent))

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

SAMPLE_RATE = 44100

# ---------------------------------------------------------------------------
# Audio helpers — used by test_acx_validator and test_audio_postprocess
# ---------------------------------------------------------------------------

try:
    import numpy as np

    def make_sine(
        frequency: float = 440.0,
        duration: float = 1.0,
        amplitude: float = 0.5,
        sr: int = SAMPLE_RATE,
    ) -> np.ndarray:
        """Generate a pure sine wave."""
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        return amplitude * np.sin(2 * np.pi * frequency * t)

    def write_wav(samples: np.ndarray, sr: int = SAMPLE_RATE) -> str:
        """Write samples to a temp WAV file and return path."""
        import soundfile as sf

        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        sf.write(path, samples, sr, subtype="PCM_16")
        return path

except ImportError:
    # numpy not installed — audio helper tests will be skipped at collection time
    pass
