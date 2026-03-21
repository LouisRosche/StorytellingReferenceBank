"""Tests for multispeaker_tts.py — SpeakerMap, generate_multispeaker_audio,
and process_manuscript_multispeaker."""

import json
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from multispeaker_tts import SpeakerMap, generate_multispeaker_audio

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


@pytest.fixture
def speaker_map(speaker_map_file):
    return SpeakerMap.from_json(speaker_map_file)


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


# ---------------------------------------------------------------------------
# generate_multispeaker_audio
# ---------------------------------------------------------------------------


class TestGenerateMultispeakerAudio:
    """Test the audio generation orchestration with mocked TTS."""

    def _make_segment(self, speaker, text, is_dialogue=False):
        seg = MagicMock()
        seg.speaker = speaker
        seg.text = text
        seg.is_dialogue = is_dialogue
        return seg

    def test_generates_audio_for_segments(self, speaker_map):
        segments = [
            self._make_segment("Narrator", "Once upon a time."),
            self._make_segment("Alice", "Hello!", is_dialogue=True),
        ]
        fake_audio = np.random.randn(22050).astype(np.float32)
        mock_persona = MagicMock()

        with (
            patch("tts_generator.Persona") as MockPersona,
            patch("tts_generator.generate_from_persona") as mock_gen,
        ):
            MockPersona.from_json.return_value = mock_persona
            mock_gen.return_value = ([fake_audio], 22050)

            result, sr = generate_multispeaker_audio(segments, speaker_map)
            assert sr == 22050
            assert len(result) == 1
            assert len(result[0]) > 0
            assert mock_gen.call_count == 2

    def test_caches_personas(self, speaker_map):
        """Same speaker should only load persona once."""
        segments = [
            self._make_segment("Narrator", "Line one."),
            self._make_segment("Narrator", "Line two."),
            self._make_segment("Narrator", "Line three."),
        ]
        fake_audio = np.random.randn(22050).astype(np.float32)
        mock_persona = MagicMock()

        with (
            patch("tts_generator.Persona") as MockPersona,
            patch("tts_generator.generate_from_persona") as mock_gen,
        ):
            MockPersona.from_json.return_value = mock_persona
            mock_gen.return_value = ([fake_audio], 22050)

            generate_multispeaker_audio(segments, speaker_map)
            # Persona loaded once for Narrator, not 3 times
            assert MockPersona.from_json.call_count == 1

    def test_raises_on_empty_segments(self, speaker_map):
        with pytest.raises(ValueError, match="No audio generated"):
            generate_multispeaker_audio([], speaker_map)

    def test_handles_tts_error_with_silence(self, speaker_map):
        """Failed segments get silence placeholders if sample_rate is known."""
        seg_ok = self._make_segment("Narrator", "Good line.")
        seg_bad = self._make_segment("Alice", "This will fail.")

        fake_audio = np.random.randn(22050).astype(np.float32)
        mock_persona = MagicMock()

        call_count = [0]

        def gen_side_effect(text, persona, lang):
            call_count[0] += 1
            if call_count[0] == 1:
                return ([fake_audio], 22050)
            raise RuntimeError("TTS engine crashed")

        with (
            patch("tts_generator.Persona") as MockPersona,
            patch("tts_generator.generate_from_persona", side_effect=gen_side_effect),
        ):
            MockPersona.from_json.return_value = mock_persona

            result, sr = generate_multispeaker_audio([seg_ok, seg_bad], speaker_map)
            assert sr == 22050
            assert len(result[0]) > len(fake_audio)  # includes silence placeholder

    def test_crossfade_between_speakers(self, speaker_map):
        """Different speakers should get crossfade transition."""
        segments = [
            self._make_segment("Narrator", "Narration."),
            self._make_segment("Alice", "Dialogue.", is_dialogue=True),
        ]
        fake_audio = np.ones(22050, dtype=np.float32) * 0.5

        with (
            patch("tts_generator.Persona") as MockPersona,
            patch("tts_generator.generate_from_persona") as mock_gen,
        ):
            MockPersona.from_json.return_value = MagicMock()
            mock_gen.return_value = ([fake_audio.copy()], 22050)

            result, sr = generate_multispeaker_audio(segments, speaker_map)
            # Result should be longer than 2x single segment due to pauses
            assert len(result[0]) > len(fake_audio)

    def test_progress_callback(self, speaker_map):
        segments = [
            self._make_segment("Narrator", "Line one."),
            self._make_segment("Narrator", "Line two."),
        ]
        fake_audio = np.random.randn(22050).astype(np.float32)
        callback = MagicMock()

        with (
            patch("tts_generator.Persona") as MockPersona,
            patch("tts_generator.generate_from_persona") as mock_gen,
        ):
            MockPersona.from_json.return_value = MagicMock()
            mock_gen.return_value = ([fake_audio], 22050)

            generate_multispeaker_audio(segments, speaker_map, progress_callback=callback)
            assert callback.call_count == 2
            callback.assert_any_call(1, 2)
            callback.assert_any_call(2, 2)

    def test_verbose_output(self, speaker_map, capsys):
        segments = [
            self._make_segment("Narrator", "A spoken line."),
        ]
        fake_audio = np.random.randn(22050).astype(np.float32)

        with (
            patch("tts_generator.Persona") as MockPersona,
            patch("tts_generator.generate_from_persona") as mock_gen,
        ):
            MockPersona.from_json.return_value = MagicMock()
            mock_gen.return_value = ([fake_audio], 22050)

            generate_multispeaker_audio(segments, speaker_map, verbose=True)
            captured = capsys.readouterr()
            assert "1/1" in captured.err

    def test_dialogue_pause_between_narration_and_dialogue(self, speaker_map):
        """Switching from narration to dialogue should insert a pause."""
        segments = [
            self._make_segment("Narrator", "Then she spoke.", is_dialogue=False),
            self._make_segment("Alice", "Hello!", is_dialogue=True),
        ]
        # Use short audio so pause is clearly measurable
        fake_audio = np.ones(1000, dtype=np.float32) * 0.5

        with (
            patch("tts_generator.Persona") as MockPersona,
            patch("tts_generator.generate_from_persona") as mock_gen,
        ):
            MockPersona.from_json.return_value = MagicMock()
            mock_gen.return_value = ([fake_audio.copy()], 22050)

            result, sr = generate_multispeaker_audio(segments, speaker_map)
            # Total should be longer than just concatenation due to dialogue pause
            expected_min = 2 * len(fake_audio)
            assert len(result[0]) > expected_min
