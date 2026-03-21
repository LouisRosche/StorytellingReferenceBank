"""Tests for validate_personas.py — persona JSON validation, discovery, and main."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from validate_personas import validate_persona, find_all_personas, main


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


# ---------------------------------------------------------------------------
# Warnings for optional fields
# ---------------------------------------------------------------------------

class TestWarnings:
    def test_empty_emotional_range_warns(self, tmp_path, schema, valid_persona_data):
        valid_persona_data["emotional_range"] = []
        path = _write_persona(tmp_path, valid_persona_data)
        issues = validate_persona(path, schema)
        warnings = [msg for sev, msg in issues if sev == "warning"]
        assert any("emotional_range" in msg for msg in warnings)

    def test_empty_use_cases_warns(self, tmp_path, schema, valid_persona_data):
        valid_persona_data["use_cases"] = []
        path = _write_persona(tmp_path, valid_persona_data)
        issues = validate_persona(path, schema)
        warnings = [msg for sev, msg in issues if sev == "warning"]
        assert any("use_cases" in msg for msg in warnings)

    def test_empty_languages_warns(self, tmp_path, schema, valid_persona_data):
        valid_persona_data["voice_attributes"]["languages"] = []
        path = _write_persona(tmp_path, valid_persona_data)
        issues = validate_persona(path, schema)
        warnings = [msg for sev, msg in issues if sev == "warning"]
        assert any("languages" in msg for msg in warnings)

    def test_invalid_model_variant_warns(self, tmp_path, schema, valid_persona_data):
        valid_persona_data["model_variant"] = "nonexistent-model"
        path = _write_persona(tmp_path, valid_persona_data)
        issues = validate_persona(path, schema)
        warnings = [msg for sev, msg in issues if sev == "warning"]
        assert any("model_variant" in msg for msg in warnings)


# ---------------------------------------------------------------------------
# quality and product nested validation
# ---------------------------------------------------------------------------

class TestNestedValidation:
    def test_invalid_validation_status(self, tmp_path, schema, valid_persona_data):
        valid_persona_data["quality"] = {"validation_status": "bogus"}
        path = _write_persona(tmp_path, valid_persona_data)
        issues = validate_persona(path, schema)
        warnings = [msg for sev, msg in issues if sev == "warning"]
        assert any("validation_status" in msg for msg in warnings)

    def test_invalid_product_tier(self, tmp_path, schema, valid_persona_data):
        valid_persona_data["product"] = {"tier": "bogus-tier"}
        path = _write_persona(tmp_path, valid_persona_data)
        issues = validate_persona(path, schema)
        warnings = [msg for sev, msg in issues if sev == "warning"]
        assert any("tier" in msg for msg in warnings)

    def test_valid_quality_block_passes(self, tmp_path, schema, valid_persona_data):
        valid_persona_data["quality"] = {}
        path = _write_persona(tmp_path, valid_persona_data)
        issues = validate_persona(path, schema)
        quality_issues = [msg for sev, msg in issues if "quality" in msg or "validation_status" in msg]
        assert quality_issues == []


# ---------------------------------------------------------------------------
# find_all_personas
# ---------------------------------------------------------------------------

class TestFindAllPersonas:
    def test_finds_example_personas(self):
        """Should find the real persona examples in the repo."""
        personas = find_all_personas()
        assert len(personas) > 0

    def test_returns_sorted_list(self):
        personas = find_all_personas()
        paths_str = [str(p) for p in personas]
        assert paths_str == sorted(paths_str)


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------

class TestMain:
    def test_validates_all_personas(self, capsys):
        """main() should validate all personas and return 0 if no errors."""
        with patch("sys.argv", ["validate_personas.py"]):
            result = main()
        captured = capsys.readouterr()
        assert "files checked" in captured.out
        # Real personas should be valid
        assert result == 0

    def test_validates_single_persona(self, tmp_path, capsys):
        persona = _write_persona(tmp_path, {
            "id": "test-single",
            "name": "Test Single",
            "voice_prompt": "A test voice.",
        })
        with patch("sys.argv", ["validate_personas.py", "--persona", str(persona)]), \
             patch("validate_personas.REPO_ROOT", tmp_path):
            result = main()
        captured = capsys.readouterr()
        assert "1 files checked" in captured.out
        assert result == 0

    def test_json_output(self, capsys):
        with patch("sys.argv", ["validate_personas.py", "--json"]):
            main()
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "total_files" in data
        assert "total_errors" in data
        assert "results" in data

    def test_returns_1_on_errors(self, tmp_path, capsys):
        bad_persona = _write_persona(tmp_path, {"status": "active"})  # missing required
        with patch("sys.argv", ["validate_personas.py", "--persona", str(bad_persona)]), \
             patch("validate_personas.REPO_ROOT", tmp_path):
            result = main()
        assert result == 1

    def test_no_personas_found(self, capsys, tmp_path):
        with patch("validate_personas.EXAMPLES_DIR", tmp_path / "nonexistent"), \
             patch("validate_personas.PROJECTS_DIR", tmp_path / "nonexistent2"), \
             patch("sys.argv", ["validate_personas.py"]):
            result = main()
        captured = capsys.readouterr()
        assert "No persona files found" in captured.out
        assert result == 1
