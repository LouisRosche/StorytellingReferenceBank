#!/usr/bin/env python3
"""
Manuscript to chapters preparation tool.

Splits manuscript files into individual chapter files for TTS processing.
Supports various chapter marker formats and picture book page-turn pauses.

Usage:
    # Split by chapter markers
    python manuscript_to_chapters.py manuscript.txt --output-dir chapters/

    # Custom chapter pattern
    python manuscript_to_chapters.py manuscript.md --pattern "^## " --output-dir chapters/

    # Picture book with page-turn pauses
    python manuscript_to_chapters.py picturebook.txt --page-turns --pause-duration 2.0

    # Generate manifest only (dry run)
    python manuscript_to_chapters.py manuscript.txt --dry-run

Chapter markers detected (in order of priority):
    - "Chapter 1", "CHAPTER ONE", "Chapter I"
    - "# Chapter", "## Chapter" (Markdown headers)
    - "---" or "***" (section breaks)
    - "[PAGE]" or "[PAGE TURN]" (picture book markers)
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime


# Common chapter patterns
CHAPTER_PATTERNS = [
    # "Chapter 1", "Chapter One", "CHAPTER 1"
    r'^(?:CHAPTER|Chapter)\s+(?:\d+|[IVXLC]+|One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|Eleven|Twelve|Thirteen|Fourteen|Fifteen|Sixteen|Seventeen|Eighteen|Nineteen|Twenty)(?:\s*[:\-–—]\s*.*)?$',
    # Markdown headers: "# Chapter", "## Title"
    r'^#{1,3}\s+.+$',
    # Section breaks
    r'^(?:\*{3,}|-{3,}|_{3,})$',
    # Explicit markers
    r'^\[(?:CHAPTER|SECTION|PART)\s*\d*\]$',
]

# Picture book specific
PAGE_TURN_PATTERNS = [
    r'\[PAGE\s*(?:TURN)?\]',
    r'\[TURN\]',
    r'---PAGE---',
    r'\*\*\*',
]

# TTS pause markers
PAUSE_MARKER = "[PAUSE {duration}s]"


@dataclass
class Chapter:
    """Represents a single chapter or section."""
    number: int
    title: str
    content: str
    start_line: int
    end_line: int
    word_count: int = 0
    has_page_turns: bool = False

    def __post_init__(self):
        self.word_count = len(self.content.split())


@dataclass
class Manifest:
    """Manifest file for chapter batch processing."""
    title: str
    source_file: str
    created_at: str
    chapters: List[dict] = field(default_factory=list)
    total_word_count: int = 0
    settings: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    def save(self, path: str):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)


def detect_chapter_pattern(text: str) -> Optional[str]:
    """
    Detect which chapter pattern is used in the manuscript.

    Returns the regex pattern that matches, or None if no pattern found.
    """
    lines = text.split('\n')

    for pattern in CHAPTER_PATTERNS:
        matches = sum(1 for line in lines if re.match(pattern, line.strip(), re.IGNORECASE))
        if matches >= 2:  # At least 2 chapters to confirm pattern
            return pattern

    return None


def split_by_pattern(text: str, pattern: str) -> List[Tuple[str, str, int]]:
    """
    Split text by regex pattern.

    Returns list of (title, content, start_line) tuples.
    """
    lines = text.split('\n')
    sections = []
    current_title = "Opening"
    current_content = []
    current_start = 0

    for i, line in enumerate(lines):
        if re.match(pattern, line.strip(), re.IGNORECASE):
            # Save previous section
            if current_content or sections:  # Don't save empty first section
                content = '\n'.join(current_content).strip()
                if content:
                    sections.append((current_title, content, current_start))

            # Start new section
            current_title = line.strip()
            current_content = []
            current_start = i
        else:
            current_content.append(line)

    # Don't forget last section
    content = '\n'.join(current_content).strip()
    if content:
        sections.append((current_title, content, current_start))

    return sections


def split_manuscript(
    text: str,
    pattern: Optional[str] = None,
    min_words: int = 50,
) -> List[Chapter]:
    """
    Split manuscript into chapters.

    Args:
        text: Full manuscript text
        pattern: Regex pattern for chapter markers (auto-detect if None)
        min_words: Minimum words to consider a valid chapter

    Returns:
        List of Chapter objects
    """
    # Auto-detect pattern if not provided
    if pattern is None:
        pattern = detect_chapter_pattern(text)

    if pattern is None:
        # No pattern found - treat as single chapter
        return [Chapter(
            number=1,
            title="Full Text",
            content=text.strip(),
            start_line=0,
            end_line=len(text.split('\n')),
        )]

    # Split by pattern
    sections = split_by_pattern(text, pattern)

    # Convert to Chapter objects
    chapters = []
    for i, (title, content, start_line) in enumerate(sections):
        # Skip very short sections (likely not real chapters)
        if len(content.split()) < min_words:
            continue

        # Clean title
        clean_title = re.sub(r'^#+\s*', '', title)  # Remove markdown headers
        clean_title = re.sub(r'^\[.*?\]\s*', '', clean_title)  # Remove markers
        clean_title = clean_title.strip()

        # Detect page turns
        has_page_turns = any(
            re.search(p, content, re.IGNORECASE)
            for p in PAGE_TURN_PATTERNS
        )

        chapters.append(Chapter(
            number=i + 1,
            title=clean_title or f"Chapter {i + 1}",
            content=content,
            start_line=start_line,
            end_line=start_line + len(content.split('\n')),
            has_page_turns=has_page_turns,
        ))

    return chapters


def insert_page_turn_pauses(
    text: str,
    pause_duration: float = 2.0,
) -> str:
    """
    Replace page turn markers with TTS pause markers.

    Args:
        text: Chapter text
        pause_duration: Pause duration in seconds

    Returns:
        Text with pause markers inserted
    """
    result = text

    for pattern in PAGE_TURN_PATTERNS:
        pause = PAUSE_MARKER.format(duration=pause_duration)
        result = re.sub(pattern, f"\n{pause}\n", result, flags=re.IGNORECASE)

    return result


def generate_acx_filename(
    title: str,
    chapter_num: int,
    chapter_title: Optional[str] = None,
) -> str:
    """
    Generate ACX-compliant filename.

    Format: Title_Chapter_01.txt (for text) or Title_Chapter_01.wav (for audio)
    """
    # Clean title for filename
    clean_title = re.sub(r'[^\w\s-]', '', title).strip()
    clean_title = re.sub(r'\s+', '_', clean_title)

    # Limit length
    if len(clean_title) > 30:
        clean_title = clean_title[:30]

    return f"{clean_title}_Chapter_{chapter_num:02d}"


def create_manifest(
    title: str,
    source_file: str,
    chapters: List[Chapter],
    output_dir: str,
    settings: dict,
) -> Manifest:
    """Create manifest for batch processing."""
    manifest = Manifest(
        title=title,
        source_file=source_file,
        created_at=datetime.now().isoformat(),
        settings=settings,
    )

    for chapter in chapters:
        base_name = generate_acx_filename(title, chapter.number, chapter.title)
        manifest.chapters.append({
            "number": chapter.number,
            "title": chapter.title,
            "text_file": f"{base_name}.txt",
            "audio_file": f"{base_name}.wav",
            "word_count": chapter.word_count,
            "has_page_turns": chapter.has_page_turns,
        })
        manifest.total_word_count += chapter.word_count

    return manifest


def process_manuscript(
    input_path: str,
    output_dir: str,
    title: Optional[str] = None,
    pattern: Optional[str] = None,
    page_turns: bool = False,
    pause_duration: float = 2.0,
    min_words: int = 50,
    dry_run: bool = False,
) -> Manifest:
    """
    Process manuscript and split into chapter files.

    Args:
        input_path: Path to manuscript file
        output_dir: Directory for output files
        title: Book title (defaults to filename)
        pattern: Chapter marker pattern (auto-detect if None)
        page_turns: Insert pause markers at page turns
        pause_duration: Duration of page-turn pauses
        min_words: Minimum words per chapter
        dry_run: Only generate manifest, don't write files

    Returns:
        Manifest object
    """
    # Read manuscript
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Derive title from filename if not provided
    if title is None:
        title = Path(input_path).stem
        title = re.sub(r'[-_]', ' ', title).title()

    # Split into chapters
    chapters = split_manuscript(text, pattern, min_words)

    if not chapters:
        raise ValueError("No chapters found in manuscript")

    print(f"Found {len(chapters)} chapters", file=sys.stderr)

    # Process chapters
    settings = {
        "pattern": pattern,
        "page_turns": page_turns,
        "pause_duration": pause_duration if page_turns else None,
        "min_words": min_words,
    }

    # Create output directory
    if not dry_run:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Create manifest
    manifest = create_manifest(title, input_path, chapters, output_dir, settings)

    # Write chapter files
    for i, chapter in enumerate(chapters):
        chapter_info = manifest.chapters[i]
        text_path = Path(output_dir) / chapter_info["text_file"]

        content = chapter.content

        # Insert page-turn pauses if requested
        if page_turns and chapter.has_page_turns:
            content = insert_page_turn_pauses(content, pause_duration)

        if not dry_run:
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  Written: {text_path}", file=sys.stderr)

    # Write manifest
    manifest_path = Path(output_dir) / "manifest.json"
    if not dry_run:
        manifest.save(str(manifest_path))
        print(f"  Manifest: {manifest_path}", file=sys.stderr)

    return manifest


def create_opening_credits(
    title: str,
    author: str,
    narrator: str,
    publisher: Optional[str] = None,
    copyright_year: Optional[int] = None,
    copyright_holder: Optional[str] = None,
) -> str:
    """Generate opening credits text for TTS."""
    lines = [title]

    if author:
        lines.append(f"Written by {author}")

    if narrator:
        lines.append(f"Narrated by {narrator}")

    if publisher:
        lines.append(f"Published by {publisher}")

    if copyright_year and copyright_holder:
        lines.append(f"Copyright {copyright_year} by {copyright_holder}")

    return "\n\n".join(lines)


def create_closing_credits(
    title: str,
    author: str,
    narrator: str,
    copyright_year: Optional[int] = None,
    copyright_holder: Optional[str] = None,
    production: Optional[str] = None,
) -> str:
    """Generate closing credits text for TTS."""
    lines = [f"This has been {title}"]

    if author:
        lines.append(f"Written by {author}")

    if narrator:
        lines.append(f"Narrated by {narrator}")

    if copyright_year and copyright_holder:
        lines.append(f"Copyright {copyright_year} by {copyright_holder}")

    if production:
        lines.append(f"Production by {production}")

    return "\n\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Split manuscript into chapters for TTS processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("input", help="Manuscript file path")
    parser.add_argument("--output-dir", "-o", default="chapters",
                        help="Output directory (default: chapters)")
    parser.add_argument("--title", help="Book title (default: derived from filename)")
    parser.add_argument("--pattern", help="Regex pattern for chapter markers (auto-detect if not specified)")

    # Picture book options
    parser.add_argument("--page-turns", action="store_true",
                        help="Insert pause markers at page turns")
    parser.add_argument("--pause-duration", type=float, default=2.0,
                        help="Page-turn pause duration in seconds (default: 2.0)")

    # Processing options
    parser.add_argument("--min-words", type=int, default=50,
                        help="Minimum words per chapter (default: 50)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Only show what would be done, don't write files")

    # Credits generation
    parser.add_argument("--author", help="Author name for credits")
    parser.add_argument("--narrator", help="Narrator name for credits")
    parser.add_argument("--publisher", help="Publisher name for credits")
    parser.add_argument("--copyright-year", type=int, help="Copyright year")
    parser.add_argument("--copyright-holder", help="Copyright holder name")
    parser.add_argument("--production", help="Production credit")

    # Output format
    parser.add_argument("--json", action="store_true",
                        help="Output manifest as JSON to stdout")

    args = parser.parse_args()

    # Validate input
    if not os.path.exists(args.input):
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        manifest = process_manuscript(
            input_path=args.input,
            output_dir=args.output_dir,
            title=args.title,
            pattern=args.pattern,
            page_turns=args.page_turns,
            pause_duration=args.pause_duration,
            min_words=args.min_words,
            dry_run=args.dry_run,
        )

        # Generate credits if author/narrator provided
        if args.author or args.narrator:
            if not args.dry_run:
                credits_dir = Path(args.output_dir)

                # Opening credits
                opening = create_opening_credits(
                    title=manifest.title,
                    author=args.author or "",
                    narrator=args.narrator or "",
                    publisher=args.publisher,
                    copyright_year=args.copyright_year,
                    copyright_holder=args.copyright_holder,
                )
                opening_path = credits_dir / f"{Path(args.input).stem}_Opening_Credits.txt"
                with open(opening_path, 'w', encoding='utf-8') as f:
                    f.write(opening)
                print(f"  Written: {opening_path}", file=sys.stderr)

                # Closing credits
                closing = create_closing_credits(
                    title=manifest.title,
                    author=args.author or "",
                    narrator=args.narrator or "",
                    copyright_year=args.copyright_year,
                    copyright_holder=args.copyright_holder,
                    production=args.production,
                )
                closing_path = credits_dir / f"{Path(args.input).stem}_Closing_Credits.txt"
                with open(closing_path, 'w', encoding='utf-8') as f:
                    f.write(closing)
                print(f"  Written: {closing_path}", file=sys.stderr)

        # Output
        if args.json:
            print(json.dumps(manifest.to_dict(), indent=2))
        else:
            print(f"\nProcessed: {manifest.title}", file=sys.stderr)
            print(f"Chapters: {len(manifest.chapters)}", file=sys.stderr)
            print(f"Total words: {manifest.total_word_count:,}", file=sys.stderr)

            if args.dry_run:
                print("\n[DRY RUN - no files written]", file=sys.stderr)
            else:
                print(f"\nOutput: {args.output_dir}/", file=sys.stderr)
                print(f"Manifest: {args.output_dir}/manifest.json", file=sys.stderr)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
