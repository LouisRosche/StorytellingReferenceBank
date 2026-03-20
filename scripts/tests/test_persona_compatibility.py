"""Tests for persona_compatibility.py — scoring personas against stories."""

import pytest
from persona_compatibility import (
    genre_match_score,
    tone_match_score,
    audience_match_score,
    compatibility_score,
    rank_personas,
    normalize_genre,
    Persona,
    StoryMeta,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def thriller_story():
    return StoryMeta(
        title="Night Run",
        genres={"thriller", "noir"},
        tones={"dark", "tense"},
        target_audience="adult",
    )


@pytest.fixture
def children_story():
    return StoryMeta(
        title="Bunny's Day",
        genres={"picture books"},
        tones={"light", "whimsical"},
        target_audience="children",
    )


@pytest.fixture
def thriller_persona():
    return Persona(
        id="dark-narrator",
        name="Dark Narrator",
        use_cases={"thriller", "noir", "horror"},
        emotional_range={"grave", "cold", "tense", "dread", "urgent", "controlled"},
    )


@pytest.fixture
def children_persona():
    return Persona(
        id="sunny-reader",
        name="Sunny Reader",
        use_cases={"picture books", "children's", "early readers"},
        emotional_range={"warm", "playful", "gentle", "bright", "wonder", "magical"},
    )


@pytest.fixture
def empty_persona():
    return Persona(id="blank", name="Blank")


# ---------------------------------------------------------------------------
# genre_match_score (Jaccard similarity)
# ---------------------------------------------------------------------------

class TestGenreMatchScore:
    def test_perfect_overlap(self, thriller_story, thriller_persona):
        """Persona whose genres fully overlap the story should score high."""
        score = genre_match_score(thriller_persona, thriller_story)
        assert score > 0.0

    def test_no_overlap(self, children_story, thriller_persona):
        """Completely disjoint genres should score 0."""
        score = genre_match_score(thriller_persona, children_story)
        assert score == 0.0

    def test_empty_genres_neutral(self, thriller_story, empty_persona):
        """If both sides have no info, should return neutral 0.5."""
        empty_story = StoryMeta(title="Empty")
        score = genre_match_score(empty_persona, empty_story)
        assert score == 0.5

    def test_partial_overlap(self, thriller_story):
        """Persona sharing some genres should score between 0 and 1."""
        partial = Persona(
            id="mixed",
            name="Mixed",
            use_cases={"thriller", "romance"},
        )
        score = genre_match_score(partial, thriller_story)
        assert 0.0 < score < 1.0


# ---------------------------------------------------------------------------
# tone_match_score (emotional coverage)
# ---------------------------------------------------------------------------

class TestToneMatchScore:
    def test_full_coverage(self, thriller_story, thriller_persona):
        """Persona covering all required emotions should score high."""
        score = tone_match_score(thriller_persona, thriller_story)
        assert score > 0.5

    def test_no_coverage(self, thriller_story, children_persona):
        """Children's persona should have little coverage of dark/tense."""
        score = tone_match_score(children_persona, thriller_story)
        assert score < 0.5

    def test_no_tones_neutral(self, empty_persona):
        """Story with no tones should return neutral 0.5."""
        story = StoryMeta(title="No Tones", tones=set())
        score = tone_match_score(empty_persona, story)
        assert score == 0.5


# ---------------------------------------------------------------------------
# audience_match_score (binary match)
# ---------------------------------------------------------------------------

class TestAudienceMatchScore:
    def test_children_match(self, children_story, children_persona):
        """Children's persona for children's story should score 1.0."""
        score = audience_match_score(children_persona, children_story)
        assert score == 1.0

    def test_children_mismatch(self, children_story, thriller_persona):
        """Thriller persona for children's story should score low (0.3)."""
        score = audience_match_score(thriller_persona, children_story)
        assert score == 0.3

    def test_adult_default(self, thriller_story, empty_persona):
        """No use-case info for adult story returns 0.7."""
        score = audience_match_score(empty_persona, thriller_story)
        assert score == 0.7


# ---------------------------------------------------------------------------
# compatibility_score (composite weighted)
# ---------------------------------------------------------------------------

class TestCompatibilityScore:
    def test_score_range(self, thriller_story, thriller_persona):
        """Score should always be between 0 and 1."""
        score = compatibility_score(thriller_persona, thriller_story)
        assert 0.0 <= score <= 1.0

    def test_good_match_beats_bad(self, thriller_story, thriller_persona, children_persona):
        """Matching persona should outscore mismatched persona."""
        good = compatibility_score(thriller_persona, thriller_story)
        bad = compatibility_score(children_persona, thriller_story)
        assert good > bad


# ---------------------------------------------------------------------------
# rank_personas (sorting)
# ---------------------------------------------------------------------------

class TestRankPersonas:
    def test_order(self, thriller_story, thriller_persona, children_persona, empty_persona):
        """Best match should be first."""
        ranked = rank_personas(
            thriller_story,
            [children_persona, empty_persona, thriller_persona],
            top_n=3,
        )
        assert ranked[0][0].id == thriller_persona.id

    def test_top_n_limits(self, thriller_story, thriller_persona, children_persona, empty_persona):
        """top_n should cap the result list."""
        ranked = rank_personas(
            thriller_story,
            [children_persona, empty_persona, thriller_persona],
            top_n=2,
        )
        assert len(ranked) == 2

    def test_empty_personas(self, thriller_story):
        """Empty persona list returns empty ranking."""
        assert rank_personas(thriller_story, [], top_n=5) == []


# ---------------------------------------------------------------------------
# normalize_genre
# ---------------------------------------------------------------------------

class TestNormalizeGenre:
    @pytest.mark.parametrize("raw,expected", [
        ("Thriller", "thriller"),
        ("sci-fi", "scifi"),
        ("literary fiction", "literary"),
        ("unknown_genre_xyz", "unknown_genre_xyz"),
    ])
    def test_mapping(self, raw, expected):
        assert normalize_genre(raw) == expected
