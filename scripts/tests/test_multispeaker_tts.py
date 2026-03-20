"""Tests for multispeaker_tts.py — SpeakerMap and config functions."""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from multispeaker_tts import SpeakerMap


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def speaker_map_file(tmp_path):
    """Create a minimal speaker map JSON file."""
    data = {
        "title": "Test Production",
        "default_persona": "personas/default.json",
        "speakers": {
            "Narrator": {
                "persona_path": "personas/narrator.json",
                "role": "narrator",
            },
            "Alice": {
                "persona_path": "personas/alice.json",
                "role": "character",
            },
            "Bob": {
                "persona_path": "",
                "role": "character",
            },
        },
        "aliases": {
            "narrator": "Narrator",
            "ALICE": "Alice",
        },
        "production_notes": {
            "crossfade_ms": 150,
            "dialogue_pause_ms": 300,
            "page_turn_pause_ms": 3000,
        },
    }
    p = tmp_path / "speakers.json"
    p.write_text(json.dumps(data))
    return str(p)


@pytest.fixture
def minimal_map_file(tmp_path):
    """Speaker map with no optional fields."""
    data = {
        "speakers": {},
    }
    p = tmp_path / "minimal.json"
    p.write_text(json.dumps(data))
    return str(p)


# ---------------------------------------------------------------------------
# SpeakerMap.from_json
# ---------------------------------------------------------------------------


class TestSpeakerMapFromJson:
    def test_loads_basic_fields(self, speaker_map_file):
        sm = SpeakerMap.from_json(speaker_map_file)
        assert sm.title == "Test Production"
        assert "Narrator" in sm.speakers
        assert "Alice" in sm.speakers
        assert "Bob" in sm.speakers

    def test_resolves_relative_persona_paths(self, speaker_map_file, tmp_path):
        sm = SpeakerMap.from_json(speaker_map_file)
        # Relative paths should be resolved relative to the JSON file's directory
        assert sm.speakers["Narrator"]["persona_path"] == str(
            tmp_path / "personas" / "narrator.json"
        )

    def test_loads_production_notes(self, speaker_map_file):
        sm = SpeakerMap.from_json(speaker_map_file)
        assert sm.crossfade_ms == 150
        assert sm.dialogue_pause_ms == 300
        assert sm.page_turn_pause_ms == 3000

    def test_defaults_for_missing_production_notes(self, minimal_map_file):
        sm = SpeakerMap.from_json(minimal_map_file)
        assert sm.crossfade_ms == 100
        assert sm.dialogue_pause_ms == 200
        assert sm.page_turn_pause_ms == 2500

    def test_defaults_for_missing_fields(self, minimal_map_file):
        sm = SpeakerMap.from_json(minimal_map_file)
        assert sm.title == "Untitled"
        assert sm.aliases == {}

    def test_aliases_loaded(self, speaker_map_file):
        sm = SpeakerMap.from_json(speaker_map_file)
        assert sm.aliases["narrator"] == "Narrator"
        assert sm.aliases["ALICE"] == "Alice"

    def test_custom_base_dir(self, speaker_map_file, tmp_path):
        custom_base = str(tmp_path / "custom")
        sm = SpeakerMap.from_json(speaker_map_file, base_dir=custom_base)
        # Persona paths should resolve relative to custom base
        assert sm.speakers["Narrator"]["persona_path"].startswith(custom_base)


# ---------------------------------------------------------------------------
# SpeakerMap.get_persona_path
# ---------------------------------------------------------------------------


class TestGetPersonaPath:
    def test_direct_lookup(self, speaker_map_file):
        sm = SpeakerMap.from_json(speaker_map_file)
        result = sm.get_persona_path("Narrator")
        assert "narrator.json" in result

    def test_case_insensitive_lookup(self, speaker_map_file):
        sm = SpeakerMap.from_json(speaker_map_file)
        result = sm.get_persona_path("narrator")  # lowercase
        assert "narrator.json" in result

    def test_alias_lookup(self, speaker_map_file):
        sm = SpeakerMap.from_json(speaker_map_file)
        # "ALICE" is an alias for "Alice"
        result = sm.get_persona_path("ALICE")
        assert "alice.json" in result

    def test_empty_persona_falls_back_to_default(self, speaker_map_file):
        sm = SpeakerMap.from_json(speaker_map_file)
        # Bob has empty persona_path
        result = sm.get_persona_path("Bob")
        assert "default" in result

    def test_unknown_speaker_returns_default(self, speaker_map_file):
        sm = SpeakerMap.from_json(speaker_map_file)
        result = sm.get_persona_path("UnknownCharacter")
        assert "default" in result

    def test_alias_case_insensitive(self, speaker_map_file):
        sm = SpeakerMap.from_json(speaker_map_file)
        # "narrator" alias should match even though stored as "narrator"
        result = sm.get_persona_path("narrator")
        assert "narrator.json" in result
