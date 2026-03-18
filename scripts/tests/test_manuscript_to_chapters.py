#!/usr/bin/env python3
"""
Unit tests for manuscript_to_chapters.py

Covers: chapter pattern detection, splitting, page-turn pauses,
credits generation, manifest creation, and ACX filename generation.

Run with: python -m pytest scripts/tests/test_manuscript_to_chapters.py -v
"""

from pathlib import Path

from manuscript_to_chapters import (
    Chapter,
    Manifest,
    detect_chapter_pattern,
    split_manuscript,
    split_by_pattern,
    insert_page_turn_pauses,
    generate_acx_filename,
    create_manifest,
    create_opening_credits,
    create_closing_credits,
)


# ---------------------------------------------------------------------------
# Chapter pattern detection
# ---------------------------------------------------------------------------

class TestDetectChapterPattern:
    def test_detects_chapter_numbering(self):
        text = """Chapter 1: The Beginning

Some content here.

Chapter 2: The Middle

More content here.

Chapter 3: The End

Final content."""
        pattern = detect_chapter_pattern(text)
        assert pattern is not None

    def test_detects_markdown_headers(self):
        text = """# Introduction

Some content.

# Part One

More content.

# Part Two

Even more content."""
        pattern = detect_chapter_pattern(text)
        assert pattern is not None

    def test_returns_none_for_no_pattern(self):
        text = "Just a simple paragraph with no chapter markers at all."
        pattern = detect_chapter_pattern(text)
        assert pattern is None

    def test_needs_minimum_two_matches(self):
        text = """Chapter 1: Only One

This manuscript has only one chapter heading.
No second heading means no confirmed pattern."""
        pattern = detect_chapter_pattern(text)
        # Only 1 match — not enough to confirm
        assert pattern is None

    def test_detects_section_breaks(self):
        text = """Opening paragraph.

---

Second section here.

---

Third section here."""
        pattern = detect_chapter_pattern(text)
        assert pattern is not None


# ---------------------------------------------------------------------------
# Manuscript splitting
# ---------------------------------------------------------------------------

class TestSplitManuscript:
    def test_single_chapter_no_markers(self):
        text = "Just a short story without any chapter markers."
        chapters = split_manuscript(text, min_words=1)
        assert len(chapters) == 1
        assert chapters[0].title == "Full Text"
        assert chapters[0].number == 1

    def test_respects_min_words(self):
        text = """# Chapter One

A long chapter with enough words to pass the minimum threshold.
This content fills the space needed for the chapter to be valid.
We need enough words here to satisfy our minimum word count requirement.

# Chapter Two

Another chapter with sufficient content to meet the minimum.
More text padding to ensure we exceed the word count threshold."""
        chapters = split_manuscript(text, min_words=5)
        assert len(chapters) >= 2

    def test_filters_short_sections(self):
        text = """# Dedication

Thanks.

# Chapter One

This is a long enough chapter with many words to satisfy the minimum
word count requirement that we have set for valid chapters in the system."""
        chapters = split_manuscript(text, min_words=15)
        # "Thanks." is only 1 word — should be filtered
        assert all(c.word_count >= 15 for c in chapters)

    def test_page_turn_detection(self):
        text = """Once upon a time.

[PAGE TURN]

The bear went for a walk.

[PAGE TURN]

The end."""
        chapters = split_manuscript(text, min_words=1)
        assert chapters[0].has_page_turns is True

    def test_no_page_turns(self):
        text = "A simple story with no page turn markers at all."
        chapters = split_manuscript(text, min_words=1)
        assert chapters[0].has_page_turns is False

    def test_chapter_word_counts(self):
        text = "One two three four five six seven eight nine ten."
        chapters = split_manuscript(text, min_words=1)
        assert chapters[0].word_count == 10

    def test_custom_pattern(self):
        text = """SCENE 1

First scene content with enough words to pass the filter.

SCENE 2

Second scene content with enough words to pass the filter."""
        chapters = split_manuscript(text, pattern=r'^SCENE \d+$', min_words=5)
        assert len(chapters) == 2

    def test_with_sample_story(self):
        """Integration test with the actual sample fixture."""
        sample_path = Path(__file__).parent / "sample_childrens_story.txt"
        if sample_path.exists():
            text = sample_path.read_text()
            chapters = split_manuscript(text, min_words=10)
            assert len(chapters) >= 1
            assert chapters[0].word_count > 0


# ---------------------------------------------------------------------------
# Split by pattern
# ---------------------------------------------------------------------------

class TestSplitByPattern:
    def test_returns_tuples(self):
        text = """# First

Content one.

# Second

Content two."""
        sections = split_by_pattern(text, r'^#\s+.+$')
        assert len(sections) == 2
        assert sections[0][0] == "# First"  # title
        assert "Content one" in sections[0][1]  # content

    def test_empty_text(self):
        sections = split_by_pattern("", r'^#\s+.+$')
        assert len(sections) == 0

    def test_no_matches(self):
        sections = split_by_pattern("Just text.", r'^CHAPTER \d+$')
        # Should still return the opening section
        assert len(sections) == 0 or sections[0][0] == "Opening"


# ---------------------------------------------------------------------------
# Page turn pauses
# ---------------------------------------------------------------------------

class TestInsertPageTurnPauses:
    def test_replaces_page_turn_marker(self):
        text = "Before.\n\n[PAGE TURN]\n\nAfter."
        result = insert_page_turn_pauses(text, pause_duration=2.0)
        assert "[PAUSE 2.0s]" in result
        assert "[PAGE TURN]" not in result

    def test_replaces_page_marker(self):
        text = "Before.\n\n[PAGE]\n\nAfter."
        result = insert_page_turn_pauses(text, pause_duration=1.5)
        assert "[PAUSE 1.5s]" in result

    def test_custom_duration(self):
        text = "Before.\n[PAGE TURN]\nAfter."
        result = insert_page_turn_pauses(text, pause_duration=3.5)
        assert "[PAUSE 3.5s]" in result

    def test_no_markers_unchanged(self):
        text = "No page turns here."
        result = insert_page_turn_pauses(text)
        assert result == text

    def test_multiple_markers(self):
        text = "A\n[PAGE TURN]\nB\n[PAGE TURN]\nC"
        result = insert_page_turn_pauses(text)
        assert result.count("[PAUSE") == 2


# ---------------------------------------------------------------------------
# ACX filename generation
# ---------------------------------------------------------------------------

class TestGenerateAcxFilename:
    def test_basic_filename(self):
        name = generate_acx_filename("My Book", 1)
        assert name == "My_Book_Chapter_01"

    def test_zero_padded(self):
        name = generate_acx_filename("Title", 5)
        assert "Chapter_05" in name

    def test_special_characters_removed(self):
        name = generate_acx_filename("Book: A Story!", 1)
        assert ":" not in name
        assert "!" not in name

    def test_long_title_truncated(self):
        name = generate_acx_filename("A" * 50, 1)
        # Title portion should be at most 30 chars
        title_part = name.split("_Chapter_")[0]
        assert len(title_part) <= 30


# ---------------------------------------------------------------------------
# Manifest creation
# ---------------------------------------------------------------------------

class TestCreateManifest:
    def test_manifest_structure(self):
        chapters = [
            Chapter(number=1, title="Ch1", content="Word " * 100,
                    start_line=0, end_line=10),
            Chapter(number=2, title="Ch2", content="Word " * 200,
                    start_line=11, end_line=20),
        ]
        manifest = create_manifest("Test Book", "test.txt", chapters, "output/", {})
        assert manifest.title == "Test Book"
        assert len(manifest.chapters) == 2
        assert manifest.total_word_count == 300

    def test_manifest_to_dict(self):
        chapters = [Chapter(number=1, title="Ch1", content="Hello world",
                            start_line=0, end_line=1)]
        manifest = create_manifest("T", "f.txt", chapters, "out/", {"page_turns": False})
        d = manifest.to_dict()
        assert isinstance(d, dict)
        assert "chapters" in d
        assert "title" in d


# ---------------------------------------------------------------------------
# Credits generation
# ---------------------------------------------------------------------------

class TestCreditsGeneration:
    def test_opening_credits(self):
        credits = create_opening_credits(
            title="My Book",
            author="Jane Doe",
            narrator="AI Voice",
        )
        assert "My Book" in credits
        assert "Jane Doe" in credits
        assert "AI Voice" in credits

    def test_opening_credits_with_copyright(self):
        credits = create_opening_credits(
            title="Book",
            author="Author",
            narrator="Narrator",
            copyright_year=2026,
            copyright_holder="Publisher Inc",
        )
        assert "2026" in credits
        assert "Publisher Inc" in credits

    def test_closing_credits(self):
        credits = create_closing_credits(
            title="My Book",
            author="Jane Doe",
            narrator="AI Voice",
        )
        assert "This has been My Book" in credits
        assert "Jane Doe" in credits

    def test_closing_credits_with_production(self):
        credits = create_closing_credits(
            title="Book",
            author="Author",
            narrator="Narrator",
            production="Studio X",
        )
        assert "Studio X" in credits

    def test_minimal_credits(self):
        # Empty author/narrator should still produce title
        credits = create_opening_credits(title="Title", author="", narrator="")
        assert "Title" in credits
