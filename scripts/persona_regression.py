#!/usr/bin/env python3
"""
Persona regression testing for bespoke reading personalities.

Validates persona consistency across updates by comparing against golden references.
"""

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

# Optional imports for audio comparison
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False


@dataclass
class RegressionResult:
    """Result of a single persona regression test."""
    persona_id: str
    passed: bool
    similarity_score: float
    threshold: float
    message: str


@dataclass
class RegressionReport:
    """Full regression report."""
    total: int
    passed: int
    failed: int
    skipped: int
    results: list[RegressionResult]

    @property
    def success_rate(self) -> float:
        return self.passed / self.total if self.total > 0 else 0.0


# Regression thresholds
SIMILARITY_THRESHOLD = 0.85  # Minimum similarity to pass
MFCC_COEFFICIENTS = 13       # For voice fingerprinting
HOP_LENGTH = 512
SAMPLE_RATE = 22050


def load_persona(path: Path) -> dict:
    """Load persona JSON."""
    with open(path) as f:
        return json.load(f)


def extract_voice_fingerprint(audio_path: Path) -> Optional[np.ndarray]:
    """Extract MFCC-based voice fingerprint from audio."""
    if not LIBROSA_AVAILABLE:
        return None

    try:
        y, sr = librosa.load(str(audio_path), sr=SAMPLE_RATE)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=MFCC_COEFFICIENTS, hop_length=HOP_LENGTH)
        # Return mean across time for stable fingerprint
        return np.mean(mfccs, axis=1)
    except Exception as e:
        print(f"Warning: Could not extract fingerprint from {audio_path}: {e}", file=sys.stderr)
        return None


def compare_fingerprints(fp1: np.ndarray, fp2: np.ndarray) -> float:
    """Compare two voice fingerprints using cosine similarity."""
    norm1 = np.linalg.norm(fp1)
    norm2 = np.linalg.norm(fp2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(fp1, fp2) / (norm1 * norm2))


def test_persona(persona_path: Path, golden_dir: Path, test_dir: Path) -> RegressionResult:
    """Run regression test for a single persona."""
    persona = load_persona(persona_path)
    persona_id = persona["id"]

    # Check for golden reference
    golden_ref = persona.get("quality", {}).get("golden_reference")
    if not golden_ref:
        return RegressionResult(
            persona_id=persona_id,
            passed=True,
            similarity_score=1.0,
            threshold=SIMILARITY_THRESHOLD,
            message="No golden reference defined (skipped)"
        )

    golden_path = golden_dir / Path(golden_ref).name
    test_path = test_dir / f"{persona_id}_test.wav"

    if not golden_path.exists():
        return RegressionResult(
            persona_id=persona_id,
            passed=True,
            similarity_score=1.0,
            threshold=SIMILARITY_THRESHOLD,
            message=f"Golden reference not found: {golden_path} (skipped)"
        )

    if not test_path.exists():
        return RegressionResult(
            persona_id=persona_id,
            passed=False,
            similarity_score=0.0,
            threshold=SIMILARITY_THRESHOLD,
            message=f"Test audio not found: {test_path}"
        )

    if not LIBROSA_AVAILABLE:
        return RegressionResult(
            persona_id=persona_id,
            passed=True,
            similarity_score=1.0,
            threshold=SIMILARITY_THRESHOLD,
            message="librosa not installed (skipped audio comparison)"
        )

    # Extract and compare fingerprints
    golden_fp = extract_voice_fingerprint(golden_path)
    test_fp = extract_voice_fingerprint(test_path)

    if golden_fp is None or test_fp is None:
        return RegressionResult(
            persona_id=persona_id,
            passed=False,
            similarity_score=0.0,
            threshold=SIMILARITY_THRESHOLD,
            message="Could not extract voice fingerprints"
        )

    similarity = compare_fingerprints(golden_fp, test_fp)
    passed = similarity >= SIMILARITY_THRESHOLD

    return RegressionResult(
        persona_id=persona_id,
        passed=passed,
        similarity_score=similarity,
        threshold=SIMILARITY_THRESHOLD,
        message="PASS" if passed else f"FAIL: similarity {similarity:.3f} < {SIMILARITY_THRESHOLD}"
    )


def run_regression(
    personas_dir: Path,
    golden_dir: Path,
    test_dir: Path,
    persona_ids: Optional[list[str]] = None
) -> RegressionReport:
    """Run regression tests for all or specified personas."""
    results = []

    # Find all persona files
    persona_files = list(personas_dir.glob("*.json"))

    for persona_file in persona_files:
        persona = load_persona(persona_file)
        persona_id = persona["id"]

        # Skip if not in specified list
        if persona_ids and persona_id not in persona_ids:
            continue

        result = test_persona(persona_file, golden_dir, test_dir)
        results.append(result)

    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed and "skipped" not in r.message.lower())
    skipped = sum(1 for r in results if "skipped" in r.message.lower())

    return RegressionReport(
        total=len(results),
        passed=passed,
        failed=failed,
        skipped=skipped,
        results=results
    )


def print_report(report: RegressionReport) -> None:
    """Print regression report."""
    print("\n" + "=" * 60)
    print("PERSONA REGRESSION REPORT")
    print("=" * 60)

    for result in report.results:
        status = "✓" if result.passed else "✗"
        print(f"{status} {result.persona_id}: {result.message}")
        if result.similarity_score < 1.0 and "skipped" not in result.message.lower():
            print(f"  Similarity: {result.similarity_score:.3f} (threshold: {result.threshold})")

    print("-" * 60)
    print(f"Total: {report.total} | Passed: {report.passed} | Failed: {report.failed} | Skipped: {report.skipped}")
    print(f"Success rate: {report.success_rate:.1%}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Persona regression testing")
    parser.add_argument(
        "--personas-dir",
        type=Path,
        default=Path("personas/examples"),
        help="Directory containing persona JSON files"
    )
    parser.add_argument(
        "--golden-dir",
        type=Path,
        default=Path("personas/golden"),
        help="Directory containing golden reference audio"
    )
    parser.add_argument(
        "--test-dir",
        type=Path,
        default=Path("test_output"),
        help="Directory containing test audio to compare"
    )
    parser.add_argument(
        "--personas",
        nargs="+",
        help="Specific persona IDs to test (default: all)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=SIMILARITY_THRESHOLD,
        help=f"Similarity threshold for pass (default: {SIMILARITY_THRESHOLD})"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    global SIMILARITY_THRESHOLD
    SIMILARITY_THRESHOLD = args.threshold

    report = run_regression(
        args.personas_dir,
        args.golden_dir,
        args.test_dir,
        args.personas
    )

    if args.json:
        output = {
            "total": report.total,
            "passed": report.passed,
            "failed": report.failed,
            "skipped": report.skipped,
            "success_rate": report.success_rate,
            "results": [
                {
                    "persona_id": r.persona_id,
                    "passed": r.passed,
                    "similarity_score": r.similarity_score,
                    "threshold": r.threshold,
                    "message": r.message
                }
                for r in report.results
            ]
        }
        print(json.dumps(output, indent=2))
    else:
        print_report(report)

    sys.exit(0 if report.failed == 0 else 1)


if __name__ == "__main__":
    main()
