#!/usr/bin/env python3
"""
Unit tests for SpeakerMap in multispeaker_tts.py

Run with: python -m pytest scripts/tests/test_speaker_map.py -v
Or: python scripts/tests/test_speaker_map.py
"""

import json
import os
import tempfile

from multispeaker_tts import SpeakerMap


class TestSpeakerMapLoading:
    """Test speaker map JSON loading."""

    def test_loads_valid_json(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "title": "Test",
                "default_persona": "personas/narrator.json",
                "speakers": {
                    "NARRATOR": {"persona_path": "personas/narrator.json"}
                },
                "aliases": {}
            }, f)
            f.flush()

            try:
                sm = SpeakerMap.from_json(f.name)
                assert sm.title == "Test"
                assert "NARRATOR" in sm.speakers
            finally:
                os.unlink(f.name)

    def test_resolves_relative_paths(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create speaker map
            map_path = os.path.join(tmpdir, "speaker-map.json")
            with open(map_path, 'w') as f:
                json.dump({
                    "title": "Test",
                    "default_persona": "personas/narrator.json",
                    "speakers": {
                        "NARRATOR": {"persona_path": "personas/narrator.json"}
                    },
                    "aliases": {}
                }, f)

            sm = SpeakerMap.from_json(map_path)

            # Path should be resolved relative to speaker-map.json location
            assert sm.default_persona == os.path.join(tmpdir, "personas/narrator.json")


class TestGetPersonaPath:
    """Test persona path lookup."""

    def setup_method(self):
        """Create a test speaker map."""
        self.speaker_map = SpeakerMap(
            title="Test",
            default_persona="/path/to/default.json",
            speakers={
                "NARRATOR": {"persona_path": "/path/to/narrator.json"},
                "SARAH": {"persona_path": "/path/to/sarah.json"},
                "THOMAS": {"persona_path": None},  # Explicitly null
                "PASTOR OAKES": {"persona_path": "/path/to/pastor.json"},
            },
            aliases={
                "dr. mercer": "SARAH",
                "pastor": "PASTOR OAKES",
            }
        )

    def test_direct_lookup_uppercase(self):
        assert self.speaker_map.get_persona_path("NARRATOR") == "/path/to/narrator.json"

    def test_case_insensitive_lookup(self):
        assert self.speaker_map.get_persona_path("narrator") == "/path/to/narrator.json"
        assert self.speaker_map.get_persona_path("Narrator") == "/path/to/narrator.json"

    def test_multiword_speaker(self):
        assert self.speaker_map.get_persona_path("PASTOR OAKES") == "/path/to/pastor.json"
        assert self.speaker_map.get_persona_path("pastor oakes") == "/path/to/pastor.json"

    def test_alias_lookup(self):
        assert self.speaker_map.get_persona_path("dr. mercer") == "/path/to/sarah.json"
        assert self.speaker_map.get_persona_path("pastor") == "/path/to/pastor.json"

    def test_null_persona_falls_back_to_default(self):
        # THOMAS has persona_path: null - should fall back to default
        assert self.speaker_map.get_persona_path("THOMAS") == "/path/to/default.json"
        assert self.speaker_map.get_persona_path("thomas") == "/path/to/default.json"

    def test_unknown_speaker_uses_default(self):
        assert self.speaker_map.get_persona_path("UNKNOWN") == "/path/to/default.json"
        assert self.speaker_map.get_persona_path("random person") == "/path/to/default.json"

    def test_alias_case_insensitive(self):
        assert self.speaker_map.get_persona_path("DR. MERCER") == "/path/to/sarah.json"
        assert self.speaker_map.get_persona_path("Dr. Mercer") == "/path/to/sarah.json"


class TestProductionNotes:
    """Test production notes parsing."""

    def test_extracts_timing_settings(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "title": "Test",
                "default_persona": "personas/narrator.json",
                "speakers": {},
                "aliases": {},
                "production_notes": {
                    "crossfade_ms": 150,
                    "dialogue_pause_ms": 300,
                    "page_turn_pause_ms": 2000
                }
            }, f)
            f.flush()

            try:
                sm = SpeakerMap.from_json(f.name)
                assert sm.crossfade_ms == 150
                assert sm.dialogue_pause_ms == 300
                assert sm.page_turn_pause_ms == 2000
            finally:
                os.unlink(f.name)

    def test_uses_defaults_when_missing(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "title": "Test",
                "default_persona": "personas/narrator.json",
                "speakers": {},
                "aliases": {}
            }, f)
            f.flush()

            try:
                sm = SpeakerMap.from_json(f.name)
                # Should use default values
                assert sm.crossfade_ms == 100
                assert sm.dialogue_pause_ms == 200
                assert sm.page_turn_pause_ms == 2500
            finally:
                os.unlink(f.name)


