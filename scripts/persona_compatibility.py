#!/usr/bin/env python3
"""
Persona-Story Compatibility Scoring

Matches stories to optimal voice personas based on genre, tone, audience,
cultural context, and language requirements.

Usage:
    python persona_compatibility.py --story story.json --personas personas/examples/
    python persona_compatibility.py --story story.json --top 3
"""

import argparse
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# Optional readability analysis for manuscript-based audience inference
try:
    import textstat
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False


# --- Tone-Emotion Mappings ---

TONE_EMOTIONS = {
    "dark": {"grave", "melancholic", "cold", "dread", "unsettling", "tense"},
    "light": {"warm", "playful", "gentle", "bright", "hopeful", "joyful"},
    "serious": {"contemplative", "grave", "measured", "honest", "weighty"},
    "humorous": {"wry", "playful", "absurd", "sardonic", "deadpan"},
    "intimate": {"tender", "vulnerable", "honest", "warm", "quiet"},
    "epic": {"heroic", "ancient", "vast", "wonder", "grave"},
    "tense": {"urgent", "controlled", "sharp", "tense", "cold"},
    "whimsical": {"playful", "wonder", "gentle", "surprised", "magical"},
}

GENRE_KEYWORDS = {
    "literary": {"literary fiction", "litfic", "literary", "memoir", "essays"},
    "thriller": {"thriller", "suspense", "noir", "mystery", "crime"},
    "romance": {"romance", "love story", "romantic"},
    "fantasy": {"fantasy", "adventure", "epic fantasy", "magical realism"},
    "scifi": {"sci-fi", "science fiction", "cyberpunk", "speculative"},
    "horror": {"horror", "dark fantasy", "gothic"},
    "children": {"picture books", "children's", "early readers", "middle grade"},
    "ya": {"YA", "young adult", "teen"},
    "nonfiction": {"nonfiction", "history", "biography", "self-help"},
    "comedy": {"comedy", "humor", "satire"},
}

AUDIENCE_TAGS = {
    "adult": {"adult", "general", "literary fiction", "memoir"},
    "ya": {"YA", "young adult", "teen", "crossover"},
    "children": {"picture books", "children's", "early readers", "middle grade"},
}


@dataclass
class StoryMeta:
    """Story metadata for compatibility scoring."""
    title: str
    genres: set = field(default_factory=set)
    tones: set = field(default_factory=set)
    target_audience: str = "adult"
    cultural_context: str = "general"
    language_needs: set = field(default_factory=lambda: {"en"})
    pov_gender: str = "mixed"

    @classmethod
    def from_dict(cls, data: dict) -> "StoryMeta":
        return cls(
            title=data.get("title", "Untitled"),
            genres=set(data.get("genres", [])),
            tones=set(data.get("tones", ["serious"])),
            target_audience=data.get("target_audience", "adult"),
            cultural_context=data.get("cultural_context", "general"),
            language_needs=set(data.get("language_needs", ["en"])),
            pov_gender=data.get("pov_gender", "mixed"),
        )


@dataclass
class Persona:
    """Voice persona for compatibility scoring."""
    id: str
    name: str
    gender: str = "neutral"
    use_cases: set = field(default_factory=set)
    emotional_range: set = field(default_factory=set)
    languages: set = field(default_factory=lambda: {"en"})
    accent: str = ""
    voice_prompt: str = ""

    @classmethod
    def from_json(cls, path: Path) -> "Persona":
        with open(path) as f:
            data = json.load(f)
        attrs = data.get("voice_attributes", {})
        return cls(
            id=data.get("id", path.stem),
            name=data.get("name", path.stem),
            gender=attrs.get("gender", "neutral"),
            use_cases=set(data.get("use_cases", [])),
            emotional_range=set(data.get("emotional_range", [])),
            languages=set(attrs.get("languages", ["en"])),
            accent=attrs.get("accent", ""),
            voice_prompt=data.get("voice_prompt", ""),
        )


def normalize_genre(genre: str) -> str:
    """Map genre string to canonical form."""
    genre_lower = genre.lower()
    for canonical, keywords in GENRE_KEYWORDS.items():
        if any(kw.lower() in genre_lower for kw in keywords):
            return canonical
    return genre_lower


def genre_match_score(persona: Persona, story: StoryMeta) -> float:
    """Jaccard similarity between persona use_cases and story genres."""
    persona_genres = {normalize_genre(uc) for uc in persona.use_cases}
    story_genres = {normalize_genre(g) for g in story.genres}
    intersection = persona_genres & story_genres
    union = persona_genres | story_genres
    if not union:
        return 0.5  # Neutral if no genre info
    return len(intersection) / len(union)


def tone_match_score(persona: Persona, story: StoryMeta) -> float:
    """How well persona's emotional range covers story's tonal needs."""
    required_emotions = set()
    for tone in story.tones:
        required_emotions.update(TONE_EMOTIONS.get(tone.lower(), set()))
    if not required_emotions:
        return 0.5
    coverage = len(persona.emotional_range & required_emotions)
    return coverage / len(required_emotions)


def audience_match_score(persona: Persona, story: StoryMeta) -> float:
    """Binary match for audience appropriateness."""
    audience_keywords = AUDIENCE_TAGS.get(story.target_audience.lower(), set())
    if any(kw.lower() in uc.lower() for uc in persona.use_cases for kw in audience_keywords):
        return 1.0
    # Neutral personas can serve any audience
    if story.target_audience == "adult":
        return 0.7
    return 0.3


def cultural_match_score(persona: Persona, story: StoryMeta) -> float:
    """Accent/cultural alignment."""
    context = story.cultural_context.lower()
    accent = persona.accent.lower()

    if context == "general" or not context:
        return 0.7  # Neutral context, most personas work
    if context in accent:
        return 1.0
    # Regional associations
    associations = {
        "american": ["american", "us", "na"],
        "british": ["british", "uk", "english"],
        "indian": ["indian"],
        "african": ["nigerian", "african", "ghanaian"],
        "caribbean": ["caribbean", "jamaican", "trinidadian"],
        "latinx": ["latinx", "latin", "spanish"],
    }
    for region, keywords in associations.items():
        if region in context and any(kw in accent for kw in keywords):
            return 1.0
    return 0.4


def language_match_score(persona: Persona, story: StoryMeta) -> float:
    """Can persona handle required languages?"""
    if story.language_needs <= persona.languages:
        return 1.0
    # Partial coverage
    coverage = len(story.language_needs & persona.languages)
    return coverage / len(story.language_needs)


def gender_match_score(persona: Persona, story: StoryMeta) -> float:
    """Soft gender preference matching."""
    pov = story.pov_gender.lower()
    pg = persona.gender.lower()
    if pov == "mixed" or pg == "neutral":
        return 0.8
    if pov == pg:
        return 1.0
    return 0.5


def compatibility_score(persona: Persona, story: StoryMeta) -> float:
    """
    Overall compatibility score (0.0 - 1.0).

    Weights:
        genre:    30%
        tone:     20%
        audience: 15%
        cultural: 15%
        language: 10%
        gender:   10%
    """
    weights = {
        "genre": 0.30,
        "tone": 0.20,
        "audience": 0.15,
        "cultural": 0.15,
        "language": 0.10,
        "gender": 0.10,
    }

    scores = {
        "genre": genre_match_score(persona, story),
        "tone": tone_match_score(persona, story),
        "audience": audience_match_score(persona, story),
        "cultural": cultural_match_score(persona, story),
        "language": language_match_score(persona, story),
        "gender": gender_match_score(persona, story),
    }

    total = sum(scores[k] * weights[k] for k in weights)
    return round(min(total, 1.0), 3)


def infer_audience_from_manuscript(text: str) -> str:
    """
    Infer target audience from manuscript text using readability metrics.

    Uses Flesch Reading Ease score mapped to audience categories:
      > 80  → children (picture books, early readers)
      60-80 → ya (young adult, accessible adult)
      30-60 → adult (standard literary fiction)
      < 30  → adult (academic, dense literary)

    The Flesch formula: 206.835 - 1.015(total_words/total_sentences)
                        - 84.6(total_syllables/total_words)
    """
    if not TEXTSTAT_AVAILABLE:
        return "adult"

    fre = textstat.flesch_reading_ease(text)
    fk_grade = textstat.flesch_kincaid_grade(text)

    if fre > 80 or fk_grade < 4:
        return "children"
    elif fre > 60 or fk_grade < 8:
        return "ya"
    else:
        return "adult"


def story_meta_from_manuscript(text: str, title: str = "Untitled") -> "StoryMeta":
    """
    Auto-generate StoryMeta from raw manuscript text using textstat analysis.

    Infers audience from readability, allowing persona matching without
    manually writing a story.json.
    """
    audience = infer_audience_from_manuscript(text)
    return StoryMeta(
        title=title,
        target_audience=audience,
    )


def load_personas(personas_dir: Path) -> list[Persona]:
    """Load all personas from directory."""
    personas = []
    for path in sorted(personas_dir.glob("*.json")):
        if path.name == "schema.json":
            continue
        try:
            personas.append(Persona.from_json(path))
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Could not load {path}: {e}")
    return personas


def rank_personas(story: StoryMeta, personas: list[Persona], top_n: int = 5) -> list[tuple[Persona, float]]:
    """Rank personas by compatibility with story."""
    scored = [(p, compatibility_score(p, story)) for p in personas]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_n]


def main():
    parser = argparse.ArgumentParser(description="Match stories to voice personas")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--story", type=Path, help="Story metadata JSON")
    group.add_argument("--manuscript", type=Path,
                       help="Manuscript text file (auto-infers audience via textstat readability)")
    parser.add_argument("--personas", type=Path, default=Path("personas/examples"),
                        help="Personas directory")
    parser.add_argument("--top", type=int, default=5, help="Number of recommendations")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    # Load story metadata — from JSON or inferred from manuscript
    if args.story:
        with open(args.story) as f:
            story = StoryMeta.from_dict(json.load(f))
    else:
        with open(args.manuscript, 'r', encoding='utf-8') as f:
            text = f.read()
        story = story_meta_from_manuscript(text, title=args.manuscript.stem)
        if not args.json:
            audience = story.target_audience
            print(f"Inferred audience from readability: {audience}")

    # Load personas
    personas = load_personas(args.personas)
    if not personas:
        print(f"No personas found in {args.personas}")
        return 1

    # Rank
    ranked = rank_personas(story, personas, args.top)

    if args.json:
        output = {
            "story": story.title,
            "recommendations": [
                {"persona_id": p.id, "name": p.name, "score": s}
                for p, s in ranked
            ]
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"\nTop {args.top} matches for \"{story.title}\":\n")
        for i, (p, score) in enumerate(ranked, 1):
            print(f"  {i}. {p.name:<30} Score: {score:.2f}")
            print(f"     {p.voice_prompt[:60]}..." if len(p.voice_prompt) > 60 else f"     {p.voice_prompt}")
            print()

    return 0


if __name__ == "__main__":
    exit(main())
