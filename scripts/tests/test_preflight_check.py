"""Tests for preflight_check.py — ValidationReport, CheckResult, check_project, find_projects."""

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from preflight_check import CheckResult, ValidationReport, check_project, find_projects


# ─── CheckResult ─────────────────────────────────────────────

class TestCheckResult:
    def test_defaults(self):
        r = CheckResult(name="test", passed=True, message="ok")
        assert r.severity == "error"
        assert r.fix_hint is None

    def test_with_fix_hint(self):
        r = CheckResult(name="t", passed=False, message="fail", fix_hint="do x")
        assert r.fix_hint == "do x"

    def test_custom_severity(self):
        r = CheckResult(name="t", passed=False, message="warn", severity="warning")
        assert r.severity == "warning"


# ─── ValidationReport ────────────────────────────────────────

class TestValidationReport:
    def test_empty_report(self):
        rpt = ValidationReport()
        assert rpt.errors == []
        assert rpt.warnings == []
        assert rpt.passed == []

    def test_add_and_categorize(self):
        rpt = ValidationReport()
        rpt.add(CheckResult("a", True, "ok"))
        rpt.add(CheckResult("b", False, "fail", severity="error"))
        rpt.add(CheckResult("c", False, "warn", severity="warning"))
        rpt.add(CheckResult("d", True, "ok"))

        assert len(rpt.passed) == 2
        assert len(rpt.errors) == 1
        assert len(rpt.warnings) == 1

    def test_print_report_returns_0_on_all_pass(self, capsys):
        rpt = ValidationReport()
        rpt.add(CheckResult("a", True, "ok"))
        assert rpt.print_report() == 0

    def test_print_report_returns_1_on_warnings_only(self, capsys):
        rpt = ValidationReport()
        rpt.add(CheckResult("a", True, "ok"))
        rpt.add(CheckResult("b", False, "warn", severity="warning"))
        assert rpt.print_report() == 1

    def test_print_report_returns_2_on_errors(self, capsys):
        rpt = ValidationReport()
        rpt.add(CheckResult("a", False, "fail", severity="error"))
        assert rpt.print_report() == 2


# ─── find_projects ────────────────────────────────────────────

class TestFindProjects:
    def test_nonexistent_base_returns_empty(self, tmp_path):
        result = find_projects(str(tmp_path / "nope"))
        assert result == []

    def test_finds_projects_with_speaker_map(self, tmp_path):
        proj = tmp_path / "projects" / "my-story"
        proj.mkdir(parents=True)
        (proj / "speaker-map.json").write_text("{}")

        result = find_projects(str(tmp_path / "projects"))
        assert len(result) == 1
        assert "my-story" in result[0]

    def test_ignores_dirs_without_speaker_map(self, tmp_path):
        proj = tmp_path / "projects" / "empty-dir"
        proj.mkdir(parents=True)

        result = find_projects(str(tmp_path / "projects"))
        assert result == []


# ─── check_project ────────────────────────────────────────────

class TestCheckProject:
    def test_missing_speaker_map(self, tmp_path):
        results = check_project(str(tmp_path))
        assert any(not r.passed for r in results)
        assert any("speaker-map" in r.name.lower() for r in results)

    def test_invalid_speaker_map_json(self, tmp_path):
        (tmp_path / "speaker-map.json").write_text("not json")
        results = check_project(str(tmp_path))
        assert any("invalid JSON" in r.message for r in results)

    def test_valid_minimal_project(self, tmp_path):
        speaker_map = {
            "default_persona": "",
            "speakers": {},
        }
        (tmp_path / "speaker-map.json").write_text(json.dumps(speaker_map))
        results = check_project(str(tmp_path))
        assert any(r.passed for r in results)

    def test_missing_persona_file(self, tmp_path):
        speaker_map = {
            "default_persona": "personas/narrator.json",
            "speakers": {},
        }
        (tmp_path / "speaker-map.json").write_text(json.dumps(speaker_map))
        results = check_project(str(tmp_path))
        assert any("file not found" in r.message for r in results)

    def test_valid_persona_file(self, tmp_path):
        persona_dir = tmp_path / "personas"
        persona_dir.mkdir()
        persona = {
            "id": "narrator-test",
            "voice_prompt": "A warm voice",
            "voice_attributes": {"pace": "moderate"},
        }
        (persona_dir / "narrator.json").write_text(json.dumps(persona))

        speaker_map = {
            "default_persona": "personas/narrator.json",
            "speakers": {
                "Narrator": {"persona_path": "personas/narrator.json"}
            },
        }
        (tmp_path / "speaker-map.json").write_text(json.dumps(speaker_map))
        results = check_project(str(tmp_path))
        # Both default persona and narrator speaker should pass
        passed = [r for r in results if r.passed]
        assert len(passed) >= 2

    def test_persona_missing_required_fields(self, tmp_path):
        persona_dir = tmp_path / "personas"
        persona_dir.mkdir()
        (persona_dir / "narrator.json").write_text(json.dumps({"id": "test"}))

        speaker_map = {
            "default_persona": "",
            "speakers": {
                "Narrator": {"persona_path": "personas/narrator.json"}
            },
        }
        (tmp_path / "speaker-map.json").write_text(json.dumps(speaker_map))
        results = check_project(str(tmp_path))
        assert any("missing fields" in r.message for r in results)

    def test_missing_drafts_directory(self, tmp_path):
        (tmp_path / "speaker-map.json").write_text(json.dumps({"speakers": {}}))
        results = check_project(str(tmp_path))
        assert any("drafts" in r.name.lower() or "missing" in r.message for r in results)
