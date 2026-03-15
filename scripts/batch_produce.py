#!/usr/bin/env python3
"""
Full audiobook production pipeline orchestrator.

Chains: manuscript_to_chapters → tts_generator → audio_postprocess → acx_validator

Produces:
- ACX-compliant chapter files (MP3)
- Opening and closing credits
- Retail sample (first 5 minutes of chapter 1)
- Full manifest with validation report

Usage:
    # Full production (requires GPU)
    python batch_produce.py manuscript.txt --persona personas/narrator.json --output-dir audiobook/

    # Dry run (validate orchestration without TTS)
    python batch_produce.py manuscript.txt --persona personas/narrator.json --dry-run

    # With metadata for credits
    python batch_produce.py manuscript.txt --persona personas/narrator.json \
        --title "My Audiobook" --author "Jane Doe" --narrator "AI Voice" \
        --output-dir audiobook/

    # Picture book with page-turn pauses
    python batch_produce.py picturebook.txt --persona personas/childrens.json \
        --page-turns --pause-duration 2.0 --output-dir audiobook/

    # Skip post-processing (for testing)
    python batch_produce.py manuscript.txt --persona personas/narrator.json \
        --no-postprocess --output-dir audiobook/

Pipeline stages:
    1. PREP: Split manuscript into chapters, generate credits text
    2. TTS: Generate raw audio for each chapter + credits
    3. MASTER: Post-process all audio for ACX compliance
    4. VALIDATE: Run ACX validator on all output files
    5. SAMPLE: Extract retail sample from chapter 1
    6. REPORT: Generate production manifest with full status
"""

import argparse
import json
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

# Add script directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


@dataclass
class ProductionConfig:
    """Configuration for the production pipeline."""
    # Source
    manuscript_path: str
    persona_path: str

    # Multispeaker
    speaker_map_path: Optional[str] = None  # Path to speaker-map.json

    # Metadata
    title: Optional[str] = None
    author: Optional[str] = None
    narrator: Optional[str] = None
    publisher: Optional[str] = None
    copyright_year: Optional[int] = None
    copyright_holder: Optional[str] = None

    # Output
    output_dir: str = "audiobook_output"

    # Processing options
    page_turns: bool = False
    pause_duration: float = 2.0
    language: str = "English"
    content_type: Optional[str] = None  # auto, childrens, literary, thriller, nonfiction

    # Pipeline control
    no_tts: bool = False  # Skip TTS generation
    no_postprocess: bool = False  # Skip post-processing
    no_validate: bool = False  # Skip validation
    keep_intermediate: bool = False  # Keep raw WAV files

    # Retail sample
    sample_duration_sec: float = 300.0  # 5 minutes


@dataclass
class ChapterStatus:
    """Status of a single chapter through the pipeline."""
    number: int
    title: str
    text_file: str
    raw_audio_file: Optional[str] = None
    final_audio_file: Optional[str] = None
    word_count: int = 0
    tts_generated: bool = False
    postprocessed: bool = False
    acx_passed: Optional[bool] = None
    acx_violations: List[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class ProductionReport:
    """Full production report."""
    title: str
    config: Dict[str, Any]
    started_at: str
    completed_at: Optional[str] = None
    chapters: List[ChapterStatus] = field(default_factory=list)
    credits: Dict[str, Any] = field(default_factory=dict)
    retail_sample: Optional[str] = None
    total_duration_sec: float = 0.0
    total_word_count: int = 0
    acx_passed: int = 0
    acx_failed: int = 0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "config": self.config,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "chapters": [asdict(c) for c in self.chapters],
            "credits": self.credits,
            "retail_sample": self.retail_sample,
            "total_duration_sec": self.total_duration_sec,
            "total_word_count": self.total_word_count,
            "acx_passed": self.acx_passed,
            "acx_failed": self.acx_failed,
            "errors": self.errors,
        }

    def save(self, path: str):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)


def stage_prep(config: ProductionConfig, report: ProductionReport, verbose: bool = False) -> Path:
    """
    Stage 1: Prepare manuscript - split into chapters, extract cues, detect content type.

    Returns path to prep directory containing chapter text files.
    """
    from manuscript_to_chapters import (
        process_manuscript,
        create_opening_credits,
        create_closing_credits,
    )
    from dialogue_parser import extract_sound_cues, strip_sound_cues
    from audio_postprocess import detect_content_type

    if verbose:
        print("\n" + "="*60)
        print("STAGE 1: PREP - Splitting manuscript")
        print("="*60)

    prep_dir = Path(config.output_dir) / "prep"
    prep_dir.mkdir(parents=True, exist_ok=True)

    # Read manuscript for cue extraction and content detection
    with open(config.manuscript_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    # Extract sound design cues before splitting
    sound_cues = extract_sound_cues(raw_text)
    if sound_cues:
        cues_path = Path(config.output_dir) / "sound_cues.json"
        with open(cues_path, 'w', encoding='utf-8') as f:
            json.dump([c.to_dict() for c in sound_cues], f, indent=2)
        report.config["sound_cues"] = str(cues_path)
        report.config["sound_cue_count"] = len(sound_cues)
        if verbose:
            print(f"  Extracted {len(sound_cues)} sound design cues → {cues_path}")

    # Auto-detect content type for mastering presets
    if config.content_type and config.content_type != "auto":
        detected_type = config.content_type
    else:
        detected_type = detect_content_type(raw_text)
    report.config["content_type"] = detected_type
    if verbose:
        print(f"  Content type: {detected_type}")

    # Strip sound cues from text before splitting for TTS
    clean_text = strip_sound_cues(raw_text)

    # Write cleaned manuscript for splitting
    clean_manuscript = prep_dir / "manuscript_clean.txt"
    with open(clean_manuscript, 'w', encoding='utf-8') as f:
        f.write(clean_text)

    # Split manuscript
    manifest = process_manuscript(
        input_path=str(clean_manuscript),
        output_dir=str(prep_dir),
        title=config.title,
        page_turns=config.page_turns,
        pause_duration=config.pause_duration,
    )

    # Update report with chapter info
    for chapter_info in manifest.chapters:
        status = ChapterStatus(
            number=chapter_info["number"],
            title=chapter_info["title"],
            text_file=str(prep_dir / chapter_info["text_file"]),
            word_count=chapter_info["word_count"],
        )
        report.chapters.append(status)
        report.total_word_count += chapter_info["word_count"]

    if verbose:
        print(f"  Split into {len(report.chapters)} chapters")
        print(f"  Total words: {report.total_word_count:,}")

    # Generate credits
    if config.author or config.narrator:
        opening = create_opening_credits(
            title=manifest.title,
            author=config.author or "",
            narrator=config.narrator or "",
            publisher=config.publisher,
            copyright_year=config.copyright_year,
            copyright_holder=config.copyright_holder,
        )
        opening_path = prep_dir / "Opening_Credits.txt"
        with open(opening_path, 'w') as f:
            f.write(opening)

        closing = create_closing_credits(
            title=manifest.title,
            author=config.author or "",
            narrator=config.narrator or "",
            copyright_year=config.copyright_year,
            copyright_holder=config.copyright_holder,
        )
        closing_path = prep_dir / "Closing_Credits.txt"
        with open(closing_path, 'w') as f:
            f.write(closing)

        report.credits = {
            "opening_text": str(opening_path),
            "closing_text": str(closing_path),
        }

        if verbose:
            print("  Generated opening and closing credits")

    return prep_dir


def _tts_single_speaker(config, report, raw_dir, verbose):
    """Generate single-speaker TTS for all chapters."""
    from tts_generator import Persona, generate_from_persona, save_audio

    persona = Persona.from_json(config.persona_path)
    if verbose:
        print(f"  Mode: single-speaker ({persona.name})")

    for chapter in report.chapters:
        if verbose:
            print(f"  Generating Chapter {chapter.number}: {chapter.title}")
        try:
            with open(chapter.text_file, 'r') as f:
                text = f.read()
            wavs, sr = generate_from_persona(text, persona, config.language)
            raw_path = raw_dir / f"Chapter_{chapter.number:02d}.wav"
            save_audio(wavs, sr, str(raw_path), normalize=False)
            chapter.raw_audio_file = str(raw_path)
            chapter.tts_generated = True
            if verbose:
                print(f"    → {raw_path}")
        except Exception as e:
            chapter.error = str(e)
            report.errors.append(f"Chapter {chapter.number} TTS failed: {e}")
            if verbose:
                print(f"    ERROR: {e}")

    # Credits use the default persona
    _tts_credits(config, report, raw_dir, verbose, persona)


def _tts_multispeaker(config, report, raw_dir, verbose):
    """Generate multi-speaker TTS using speaker-map routing."""
    from tts_generator import Persona, save_audio
    from multispeaker_tts import SpeakerMap, generate_multispeaker_audio
    from dialogue_parser import parse_manuscript

    speaker_map = SpeakerMap.from_json(config.speaker_map_path)
    if verbose:
        print(f"  Mode: multispeaker ({len(speaker_map.speakers)} speakers)")

    for chapter in report.chapters:
        if verbose:
            print(f"  Generating Chapter {chapter.number}: {chapter.title}")
        try:
            with open(chapter.text_file, 'r') as f:
                text = f.read()

            # Parse into speaker segments
            segments, stats = parse_manuscript(
                text,
                aliases=speaker_map.aliases,
            )

            if verbose:
                speakers_in_ch = list(stats.keys())
                print(f"    Speakers: {', '.join(speakers_in_ch)}")

            # Generate multispeaker audio
            wavs, sr = generate_multispeaker_audio(
                segments,
                speaker_map,
                language=config.language,
                verbose=verbose,
            )

            raw_path = raw_dir / f"Chapter_{chapter.number:02d}.wav"
            save_audio(wavs, sr, str(raw_path), normalize=False)
            chapter.raw_audio_file = str(raw_path)
            chapter.tts_generated = True
            if verbose:
                print(f"    → {raw_path}")

        except Exception as e:
            chapter.error = str(e)
            report.errors.append(f"Chapter {chapter.number} TTS failed: {e}")
            if verbose:
                print(f"    ERROR: {e}")

    # Credits use the default persona from the speaker map
    default_persona_path = speaker_map.default_persona
    from tts_generator import Persona
    persona = Persona.from_json(default_persona_path)
    _tts_credits(config, report, raw_dir, verbose, persona)


def _tts_credits(config, report, raw_dir, verbose, persona):
    """Generate TTS for opening/closing credits."""
    from tts_generator import generate_from_persona, save_audio

    for credit_type, raw_key in [("opening_text", "opening_raw"), ("closing_text", "closing_raw")]:
        credit_path = report.credits.get(credit_type)
        if not credit_path:
            continue
        label = credit_type.replace("_text", "").replace("_", " ").title()
        if verbose:
            print(f"  Generating {label} Credits")
        try:
            with open(credit_path, 'r') as f:
                text = f.read()
            wavs, sr = generate_from_persona(text, persona, config.language)
            raw_path = raw_dir / f"{label.replace(' ', '_')}_Credits.wav"
            save_audio(wavs, sr, str(raw_path), normalize=False)
            report.credits[raw_key] = str(raw_path)
        except Exception as e:
            report.errors.append(f"{label} credits TTS failed: {e}")


def stage_tts(config: ProductionConfig, report: ProductionReport, verbose: bool = False) -> Path:
    """
    Stage 2: Generate TTS audio for all chapters and credits.

    Routes to single-speaker or multispeaker pipeline based on config.speaker_map_path.

    Returns path to raw audio directory.
    """
    if config.no_tts:
        if verbose:
            print("\n" + "="*60)
            print("STAGE 2: TTS - SKIPPED (--no-tts)")
            print("="*60)
        return Path(config.output_dir) / "raw_audio"

    if verbose:
        print("\n" + "="*60)
        print("STAGE 2: TTS - Generating audio")
        print("="*60)

    raw_dir = Path(config.output_dir) / "raw_audio"
    raw_dir.mkdir(parents=True, exist_ok=True)

    if config.speaker_map_path:
        _tts_multispeaker(config, report, raw_dir, verbose)
    else:
        _tts_single_speaker(config, report, raw_dir, verbose)

    return raw_dir


def stage_master(config: ProductionConfig, report: ProductionReport, verbose: bool = False) -> Path:
    """
    Stage 3: Post-process all audio for ACX compliance.

    Returns path to final audio directory.
    """
    if config.no_postprocess:
        if verbose:
            print("\n" + "="*60)
            print("STAGE 3: MASTER - SKIPPED (--no-postprocess)")
            print("="*60)
        # Copy raw to final if skipping
        final_dir = Path(config.output_dir) / "final"
        final_dir.mkdir(parents=True, exist_ok=True)
        for chapter in report.chapters:
            if chapter.raw_audio_file and Path(chapter.raw_audio_file).exists():
                final_path = final_dir / f"Chapter_{chapter.number:02d}.mp3"
                # Would need to convert WAV to MP3 here, but skip for simplicity
                chapter.final_audio_file = chapter.raw_audio_file
        return final_dir

    from audio_postprocess import process_file, ProcessingParams, get_content_params

    if verbose:
        print("\n" + "="*60)
        print("STAGE 3: MASTER - Post-processing for ACX")
        print("="*60)

    final_dir = Path(config.output_dir) / "final"
    final_dir.mkdir(parents=True, exist_ok=True)

    # Use content-type preset if detected
    content_type = report.config.get("content_type", "literary")
    params = get_content_params(content_type)
    if verbose:
        print(f"  Mastering preset: {content_type}")

    # Process chapters
    for chapter in report.chapters:
        if not chapter.raw_audio_file or not Path(chapter.raw_audio_file).exists():
            if verbose:
                print(f"  Skipping Chapter {chapter.number} (no raw audio)")
            continue

        try:
            final_path = final_dir / f"Chapter_{chapter.number:02d}.mp3"

            if verbose:
                print(f"  Processing Chapter {chapter.number}")

            process_file(chapter.raw_audio_file, str(final_path), params, verbose=False)

            chapter.final_audio_file = str(final_path)
            chapter.postprocessed = True

            if verbose:
                print(f"    → {final_path}")

        except Exception as e:
            chapter.error = str(e)
            report.errors.append(f"Chapter {chapter.number} mastering failed: {e}")
            if verbose:
                print(f"    ERROR: {e}")

    # Process credits
    if report.credits.get("opening_raw") and Path(report.credits["opening_raw"]).exists():
        try:
            final_path = final_dir / "Opening_Credits.mp3"
            process_file(report.credits["opening_raw"], str(final_path), params, verbose=False)
            report.credits["opening_final"] = str(final_path)
            if verbose:
                print(f"  Processed Opening Credits → {final_path}")
        except Exception as e:
            report.errors.append(f"Opening credits mastering failed: {e}")

    if report.credits.get("closing_raw") and Path(report.credits["closing_raw"]).exists():
        try:
            final_path = final_dir / "Closing_Credits.mp3"
            process_file(report.credits["closing_raw"], str(final_path), params, verbose=False)
            report.credits["closing_final"] = str(final_path)
            if verbose:
                print(f"  Processed Closing Credits → {final_path}")
        except Exception as e:
            report.errors.append(f"Closing credits mastering failed: {e}")

    return final_dir


def stage_validate(config: ProductionConfig, report: ProductionReport, verbose: bool = False):
    """
    Stage 4: Validate all final audio against ACX specs.
    """
    if config.no_validate:
        if verbose:
            print("\n" + "="*60)
            print("STAGE 4: VALIDATE - SKIPPED (--no-validate)")
            print("="*60)
        return

    from acx_validator import validate_audio

    if verbose:
        print("\n" + "="*60)
        print("STAGE 4: VALIDATE - Checking ACX compliance")
        print("="*60)

    # Validate chapters
    for chapter in report.chapters:
        if not chapter.final_audio_file or not Path(chapter.final_audio_file).exists():
            continue

        try:
            validation = validate_audio(chapter.final_audio_file)

            chapter.acx_passed = validation.passed

            if validation.passed:
                report.acx_passed += 1
                if verbose:
                    print(f"  Chapter {chapter.number}: PASSED")
            else:
                report.acx_failed += 1
                chapter.acx_violations = [
                    f"{c.name}: {c.message}"
                    for c in validation.checks
                    if c.severity.value == "fail"
                ]
                if verbose:
                    print(f"  Chapter {chapter.number}: FAILED")
                    for v in chapter.acx_violations:
                        print(f"    - {v}")

        except Exception as e:
            chapter.error = str(e)
            report.errors.append(f"Chapter {chapter.number} validation failed: {e}")

    # Validate credits
    for credit_type in ["opening_final", "closing_final"]:
        credit_path = report.credits.get(credit_type)
        if credit_path and Path(credit_path).exists():
            try:
                validation = validate_audio(credit_path)
                status = "PASSED" if validation.passed else "FAILED"
                if verbose:
                    print(f"  {credit_type}: {status}")
            except Exception as e:
                report.errors.append(f"{credit_type} validation failed: {e}")


def stage_sample(config: ProductionConfig, report: ProductionReport, verbose: bool = False):
    """
    Stage 5: Extract retail sample from chapter 1.

    ACX requires a 1-5 minute sample:
    - No opening credits
    - No music
    - No explicit content
    - Begins with narration
    """
    if verbose:
        print("\n" + "="*60)
        print("STAGE 5: SAMPLE - Creating retail sample")
        print("="*60)

    # Find chapter 1
    chapter_1 = next((c for c in report.chapters if c.number == 1), None)

    if not chapter_1 or not chapter_1.final_audio_file:
        report.errors.append("Cannot create retail sample: Chapter 1 not available")
        if verbose:
            print("  ERROR: Chapter 1 not available")
        return

    if not Path(chapter_1.final_audio_file).exists():
        report.errors.append("Cannot create retail sample: Chapter 1 file not found")
        if verbose:
            print("  ERROR: Chapter 1 file not found")
        return

    try:
        from pydub import AudioSegment
    except ImportError:
        report.errors.append("Cannot create retail sample: pydub not installed")
        if verbose:
            print("  ERROR: pydub not installed")
        return

    try:
        # Load chapter 1
        audio = AudioSegment.from_file(chapter_1.final_audio_file)

        # Extract first N seconds (or entire file if shorter)
        sample_ms = int(config.sample_duration_sec * 1000)
        sample = audio[:sample_ms]

        # Add fade out at end
        fade_duration = min(2000, len(sample) // 4)  # 2 second fade or 25% of length
        sample = sample.fade_out(fade_duration)

        # Save
        sample_path = Path(config.output_dir) / "final" / "Retail_Sample.mp3"
        sample.export(
            str(sample_path),
            format="mp3",
            bitrate="192k",
        )

        report.retail_sample = str(sample_path)

        if verbose:
            print(f"  Created: {sample_path}")
            print(f"  Duration: {len(sample)/1000:.1f}s")

    except Exception as e:
        report.errors.append(f"Retail sample creation failed: {e}")
        if verbose:
            print(f"  ERROR: {e}")


def stage_cleanup(config: ProductionConfig, report: ProductionReport, verbose: bool = False):
    """
    Stage 6: Clean up intermediate files and generate final report.
    """
    if verbose:
        print("\n" + "="*60)
        print("STAGE 6: CLEANUP - Finalizing")
        print("="*60)

    # Remove intermediate files unless --keep-intermediate
    if not config.keep_intermediate:
        raw_dir = Path(config.output_dir) / "raw_audio"
        if raw_dir.exists():
            shutil.rmtree(raw_dir)
            if verbose:
                print("  Removed raw audio directory")

    # Calculate total duration from final files
    try:
        from pydub import AudioSegment

        for chapter in report.chapters:
            if chapter.final_audio_file and Path(chapter.final_audio_file).exists():
                audio = AudioSegment.from_file(chapter.final_audio_file)
                report.total_duration_sec += len(audio) / 1000
    except:
        pass

    # Set completion time
    report.completed_at = datetime.now().isoformat()

    # Save report
    report_path = Path(config.output_dir) / "production_report.json"
    report.save(str(report_path))

    if verbose:
        print(f"  Saved report: {report_path}")


def print_summary(report: ProductionReport):
    """Print human-readable summary."""
    print("\n" + "="*60)
    print("PRODUCTION COMPLETE")
    print("="*60)

    print(f"\nTitle: {report.title}")
    print(f"Chapters: {len(report.chapters)}")
    print(f"Total words: {report.total_word_count:,}")
    print(f"Total duration: {report.total_duration_sec/60:.1f} minutes")

    print(f"\nACX Validation:")
    print(f"  Passed: {report.acx_passed}")
    print(f"  Failed: {report.acx_failed}")

    if report.errors:
        print(f"\nErrors ({len(report.errors)}):")
        for e in report.errors:
            print(f"  - {e}")

    # List failed chapters
    failed = [c for c in report.chapters if c.acx_passed is False]
    if failed:
        print(f"\nFailed chapters requiring review:")
        for c in failed:
            print(f"  Chapter {c.number}: {c.title}")
            for v in c.acx_violations:
                print(f"    - {v}")

    print("\n" + "="*60)


def run_pipeline(config: ProductionConfig, verbose: bool = False) -> ProductionReport:
    """Run the full production pipeline."""
    # Initialize report
    report = ProductionReport(
        title=config.title or Path(config.manuscript_path).stem,
        config={
            "manuscript": config.manuscript_path,
            "persona": config.persona_path,
            "speaker_map": config.speaker_map_path,
            "page_turns": config.page_turns,
            "language": config.language,
        },
        started_at=datetime.now().isoformat(),
    )

    # Create output directory
    Path(config.output_dir).mkdir(parents=True, exist_ok=True)

    # Run stages
    try:
        stage_prep(config, report, verbose)
        stage_tts(config, report, verbose)
        stage_master(config, report, verbose)
        stage_validate(config, report, verbose)
        stage_sample(config, report, verbose)
        stage_cleanup(config, report, verbose)
    except Exception as e:
        report.errors.append(f"Pipeline failed: {e}")
        report.completed_at = datetime.now().isoformat()

        # Save partial report
        report_path = Path(config.output_dir) / "production_report.json"
        report.save(str(report_path))

        raise

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Full audiobook production pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Required
    parser.add_argument("manuscript", help="Path to manuscript file")
    parser.add_argument("--persona", required=True, help="Path to persona JSON file")
    parser.add_argument("--output-dir", "-o", default="audiobook_output",
                        help="Output directory (default: audiobook_output)")

    # Metadata
    parser.add_argument("--title", help="Book title")
    parser.add_argument("--author", help="Author name")
    parser.add_argument("--narrator", help="Narrator name")
    parser.add_argument("--publisher", help="Publisher name")
    parser.add_argument("--copyright-year", type=int, help="Copyright year")
    parser.add_argument("--copyright-holder", help="Copyright holder")

    # Multispeaker
    parser.add_argument("--speaker-map", help="Path to speaker-map.json for multi-voice production")

    # Processing options
    parser.add_argument("--page-turns", action="store_true",
                        help="Insert pauses at page turns (picture books)")
    parser.add_argument("--pause-duration", type=float, default=2.0,
                        help="Page-turn pause duration in seconds (default: 2.0)")
    parser.add_argument("--language", default="English",
                        help="Language for TTS (default: English)")
    parser.add_argument("--content-type",
                        choices=["auto", "childrens", "literary", "thriller", "nonfiction"],
                        default="auto",
                        help="Content type for mastering presets (default: auto-detect)")

    # Pipeline control
    parser.add_argument("--dry-run", "--no-tts", action="store_true",
                        help="Skip TTS generation (test orchestration)")
    parser.add_argument("--no-postprocess", action="store_true",
                        help="Skip audio post-processing")
    parser.add_argument("--no-validate", action="store_true",
                        help="Skip ACX validation")
    parser.add_argument("--keep-intermediate", action="store_true",
                        help="Keep raw WAV files")

    # Output
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose output")
    parser.add_argument("--json", action="store_true",
                        help="Output report as JSON")

    args = parser.parse_args()

    # Validate inputs
    if not os.path.exists(args.manuscript):
        print(f"Error: Manuscript not found: {args.manuscript}", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(args.persona):
        print(f"Error: Persona not found: {args.persona}", file=sys.stderr)
        sys.exit(1)

    # Validate speaker map if provided
    if args.speaker_map and not os.path.exists(args.speaker_map):
        print(f"Error: Speaker map not found: {args.speaker_map}", file=sys.stderr)
        sys.exit(1)

    # Build config
    config = ProductionConfig(
        manuscript_path=args.manuscript,
        persona_path=args.persona,
        speaker_map_path=args.speaker_map,
        output_dir=args.output_dir,
        title=args.title,
        author=args.author,
        narrator=args.narrator,
        publisher=args.publisher,
        copyright_year=args.copyright_year,
        copyright_holder=args.copyright_holder,
        page_turns=args.page_turns,
        pause_duration=args.pause_duration,
        language=args.language,
        content_type=args.content_type,
        no_tts=args.dry_run,
        no_postprocess=args.no_postprocess,
        no_validate=args.no_validate,
        keep_intermediate=args.keep_intermediate,
    )

    # Run pipeline
    try:
        report = run_pipeline(config, args.verbose)

        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            print_summary(report)

        # Exit code based on validation results
        if report.acx_failed > 0 or report.errors:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
