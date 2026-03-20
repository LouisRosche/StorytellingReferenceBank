"""Tests for validate_personas.py — persona JSON validation."""

import json
import pytest
from pathlib import Path

from validate_personas import validate_persona


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def schema():
    """Load the real persona schema."""
    schema_path = Path(__file__).parent.parent.parent / "personas" / "schema.json"
    with open(schema_path) as f:
        return json.load(f)


@pytest.fixture
def valid_persona_data():
    return {
        "id": "test-narrator",
        "name": "Test Narrator",
        "version": "1.0.0",
        "status": "active",
        "voice_prompt": "A warm, steady narrator voice.",
        "voice_attributes": {
            "languages": ["en"],
        },
        "emotional_range": ["warm", "steady"],
        "use_cases": ["narration"],
    }


def _write_persona(tmp_path, data, name="test.json"):
    path = tmp_path / name
    path.write_text(json.dumps(data))
    return path


# ---------------------------------------------------------------------------
# Valid persona
# ---------------------------------------------------------------------------

class TestValidPersona:
    def test_valid_passes(self, tmp_path, schema, valid_persona_data):
        path = _write_persona(tmp_path, valid_persona_data)
        issues = validate_persona(path, schema)
        errors = [msg for sev, msg in issues if sev == "error"]
        assert errors == []

    def test_minimal_valid(self, tmp_path, schema):
        """Only required fields present should pass."""
        data = {
            "id": "minimal",
            "name": "Minimal",
            "voice_prompt": "A voice.",
        }
        path = _write_persona(tmp_path, data)
        issues = validate_persona(path, schema)
        errors = [msg for sev, msg in issues if sev == "error"]
        assert errors == []


# ---------------------------------------------------------------------------
# Missing required fields
# ---------------------------------------------------------------------------

class TestMissingFields:
    def test_missing_id(self, tmp_path, schema):
        data = {"name": "No ID", "voice_prompt": "A voice."}
        path = _write_persona(tmp_path, data)
        issues = validate_persona(path, schema)
        errors = [msg for sev, msg in issues if sev == "error"]
        assert any("id" in msg for msg in errors)

    def test_missing_name(self, tmp_path, schema):
        data = {"id": "no-name", "voice_prompt": "A voice."}
        path = _write_persona(tmp_path, data)
        issues = validate_persona(path, schema)
        errors = [msg for sev, msg in issues if sev == "error"]
        assert any("name" in msg for msg in errors)

    def test_missing_voice_prompt(self, tmp_path, schema):
        data = {"id": "no-prompt", "name": "No Prompt"}
        path = _write_persona(tmp_path, data)
        issues = validate_persona(path, schema)
        errors = [msg for sev, msg in issues if sev == "error"]
        assert any("voice_prompt" in msg for msg in errors)

    def test_missing_all_required(self, tmp_path, schema):
        data = {"status": "active"}
        path = _write_persona(tmp_path, data)
        issues = validate_persona(path, schema)
        errors = [msg for sev, msg in issues if sev == "error"]
        assert len(errors) >= 3


# ---------------------------------------------------------------------------
# Invalid field types
# ---------------------------------------------------------------------------

class TestInvalidTypes:
    def test_emotional_range_not_list(self, tmp_path, schema, valid_persona_data):
        valid_persona_data["emotional_range"] = "warm"  # should be list
        path = _write_persona(tmp_path, valid_persona_data)
        issues = validate_persona(path, schema)
        errors = [msg for sev, msg in issues if sev == "error"]
        assert any("emotional_range" in msg for msg in errors)

    def test_use_cases_not_list(self, tmp_path, schema, valid_persona_data):
        valid_persona_data["use_cases"] = "narration"  # should be list
        path = _write_persona(tmp_path, valid_persona_data)
        issues = validate_persona(path, schema)
        errors = [msg for sev, msg in issues if sev == "error"]
        assert any("use_cases" in msg for msg in errors)

    def test_languages_not_list(self, tmp_path, schema, valid_persona_data):
        valid_persona_data["voice_attributes"]["languages"] = "en"  # should be list
        path = _write_persona(tmp_path, valid_persona_data)
        issues = validate_persona(path, schema)
        errors = [msg for sev, msg in issues if sev == "error"]
        assert any("languages" in msg for msg in errors)

    def test_empty_voice_prompt(self, tmp_path, schema, valid_persona_data):
        valid_persona_data["voice_prompt"] = "   "
        path = _write_persona(tmp_path, valid_persona_data)
        issues = validate_persona(path, schema)
        errors = [msg for sev, msg in issues if sev == "error"]
        assert any("voice_prompt" in msg for msg in errors)


# ---------------------------------------------------------------------------
# Pattern validation (id, version)
# ---------------------------------------------------------------------------

class TestPatternValidation:
    def test_invalid_id_uppercase(self, tmp_path, schema, valid_persona_data):
        valid_persona_data["id"] = "INVALID_ID"
        path = _write_persona(tmp_path, valid_persona_data)
        issues = validate_persona(path, schema)
        errors = [msg for sev, msg in issues if sev == "error"]
        assert any("id" in msg and "pattern" in msg for msg in errors)

    def test_invalid_id_spaces(self, tmp_path, schema, valid_persona_data):
        valid_persona_data["id"] = "has spaces"
        path = _write_persona(tmp_path, valid_persona_data)
        issues = validate_persona(path, schema)
        errors = [msg for sev, msg in issues if sev == "error"]
        assert any("id" in msg for msg in errors)

    def test_invalid_version(self, tmp_path, schema, valid_persona_data):
        valid_persona_data["version"] = "v1"
        path = _write_persona(tmp_path, valid_persona_data)
        issues = validate_persona(path, schema)
        warnings = [msg for sev, msg in issues if sev == "warning"]
        assert any("version" in msg for msg in warnings)

    def test_valid_version_passes(self, tmp_path, schema, valid_persona_data):
        valid_persona_data["version"] = "2.1.0"
        path = _write_persona(tmp_path, valid_persona_data)
        issues = validate_persona(path, schema)
        version_issues = [msg for sev, msg in issues if "version" in msg]
        assert version_issues == []

    def test_invalid_status_enum(self, tmp_path, schema, valid_persona_data):
        valid_persona_data["status"] = "archived"
        path = _write_persona(tmp_path, valid_persona_data)
        issues = validate_persona(path, schema)
        errors = [msg for sev, msg in issues if sev == "error"]
        assert any("status" in msg for msg in errors)


# ---------------------------------------------------------------------------
# Malformed JSON
# ---------------------------------------------------------------------------

class TestMalformedJSON:
    def test_invalid_json(self, tmp_path, schema):
        path = tmp_path / "bad.json"
        path.write_text("{not valid json")
        issues = validate_persona(path, schema)
        assert len(issues) == 1
        assert issues[0][0] == "error"
        assert "Invalid JSON" in issues[0][1]
