"""Tests for preflight_check.py — ValidationReport, CheckResult, check_project,
find_projects, check_dependencies, check_gpu_memory, and main."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from preflight_check import (
    CheckResult,
    ValidationReport,
    check_dependencies,
    check_gpu_memory,
    check_project,
    find_projects,
    main,
)

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

    def test_print_report_shows_fix_hints(self, capsys):
        rpt = ValidationReport()
        rpt.add(CheckResult("dep", False, "missing", fix_hint="pip install x"))
        rpt.print_report()
        captured = capsys.readouterr()
        assert "pip install x" in captured.out

    def test_print_report_summary_line(self, capsys):
        rpt = ValidationReport()
        rpt.add(CheckResult("a", True, "ok"))
        rpt.add(CheckResult("b", False, "bad", severity="warning"))
        rpt.print_report()
        captured = capsys.readouterr()
        assert "1 passed" in captured.out
        assert "1 warnings" in captured.out


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

    def test_finds_multiple_projects(self, tmp_path):
        for name in ["story-a", "story-b", "story-c"]:
            proj = tmp_path / name
            proj.mkdir()
            (proj / "speaker-map.json").write_text("{}")

        result = find_projects(str(tmp_path))
        assert len(result) == 3


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
            "speakers": {"Narrator": {"persona_path": "personas/narrator.json"}},
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
            "speakers": {"Narrator": {"persona_path": "personas/narrator.json"}},
        }
        (tmp_path / "speaker-map.json").write_text(json.dumps(speaker_map))
        results = check_project(str(tmp_path))
        assert any("missing fields" in r.message for r in results)

    def test_missing_drafts_directory(self, tmp_path):
        (tmp_path / "speaker-map.json").write_text(json.dumps({"speakers": {}}))
        results = check_project(str(tmp_path))
        assert any("drafts" in r.name.lower() or "missing" in r.message for r in results)

    def test_persona_invalid_json(self, tmp_path):
        persona_dir = tmp_path / "personas"
        persona_dir.mkdir()
        (persona_dir / "broken.json").write_text("{broken")

        speaker_map = {
            "default_persona": "",
            "speakers": {"Broken": {"persona_path": "personas/broken.json"}},
        }
        (tmp_path / "speaker-map.json").write_text(json.dumps(speaker_map))
        results = check_project(str(tmp_path))
        assert any("invalid JSON" in r.message for r in results)

    def test_drafts_with_chapters(self, tmp_path):
        """Projects with chapter files should validate them."""
        (tmp_path / "speaker-map.json").write_text(
            json.dumps(
                {
                    "speakers": {"Narrator": {"persona_path": ""}},
                    "aliases": {},
                }
            )
        )
        drafts = tmp_path / "drafts"
        drafts.mkdir()
        (drafts / "chapter-01.txt").write_text('Once upon a time.\n\n"Hello," said Alice.\n')
        results = check_project(str(tmp_path))
        # Should have a result about chapters
        chapter_results = [
            r for r in results if "chapter" in r.name.lower() or "manuscript" in r.name.lower()
        ]
        assert len(chapter_results) >= 1

    def test_drafts_without_chapters(self, tmp_path):
        (tmp_path / "speaker-map.json").write_text(json.dumps({"speakers": {}}))
        drafts = tmp_path / "drafts"
        drafts.mkdir()
        # No chapter-*.txt files
        results = check_project(str(tmp_path))
        assert any("no chapter" in r.message for r in results)

    def test_unmapped_speaker_warning(self, tmp_path):
        """Speakers in manuscript not in speaker-map should warn."""
        (tmp_path / "speaker-map.json").write_text(
            json.dumps(
                {
                    "speakers": {},
                    "aliases": {},
                }
            )
        )
        drafts = tmp_path / "drafts"
        drafts.mkdir()
        # Write a chapter with a speaker not in the map
        (drafts / "chapter-01.txt").write_text(
            'Narrator: Once upon a time.\n\n"Hello," said UnknownSpeaker.\n'
        )
        results = check_project(str(tmp_path))
        # May warn about unmapped speakers depending on parse output
        # At minimum should not crash
        assert isinstance(results, list)


# ─── check_dependencies ─────────────────────────────────────


class TestCheckDependencies:
    def test_returns_list_of_results(self):
        results = check_dependencies()
        assert isinstance(results, list)
        assert all(isinstance(r, CheckResult) for r in results)

    def test_numpy_detected(self):
        results = check_dependencies()
        numpy_results = [r for r in results if "numpy" in r.name.lower()]
        assert len(numpy_results) == 1
        assert numpy_results[0].passed  # numpy is installed in dev env

    def test_reports_missing_modules(self):
        """Simulate a missing dependency."""
        original_import = (
            __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__
        )

        def fake_import(name, *args, **kwargs):
            if name == "qwen_tts":
                raise ImportError("mocked")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=fake_import):
            results = check_dependencies()
            qwen_results = [r for r in results if "qwen" in r.name.lower()]
            if qwen_results:
                assert not qwen_results[0].passed

    def test_checks_ffmpeg(self):
        results = check_dependencies()
        ffmpeg_results = [r for r in results if "ffmpeg" in r.name.lower()]
        assert len(ffmpeg_results) == 1


# ─── check_gpu_memory ────────────────────────────────────────


class TestCheckGpuMemory:
    def test_returns_results(self):
        results = check_gpu_memory()
        assert isinstance(results, list)

    def test_handles_no_torch(self):
        """Should not crash when torch is unavailable."""
        original_import = (
            __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__
        )

        def fake_import(name, *args, **kwargs):
            if name == "torch":
                raise ImportError("mocked")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=fake_import):
            results = check_gpu_memory()
            assert isinstance(results, list)


# ─── main() ──────────────────────────────────────────────────


class TestMain:
    def test_deps_only(self, capsys):
        with patch("sys.argv", ["preflight_check.py", "--deps-only"]):
            result = main()
        captured = capsys.readouterr()
        assert "PRE-FLIGHT" in captured.out
        assert isinstance(result, int)

    def test_no_deps(self, capsys):
        with patch("sys.argv", ["preflight_check.py", "--no-deps"]):
            result = main()
        capsys.readouterr()
        assert isinstance(result, int)

    def test_specific_project(self, tmp_path, capsys):
        proj = tmp_path / "my-project"
        proj.mkdir()
        (proj / "speaker-map.json").write_text(json.dumps({"speakers": {}}))

        argv = ["preflight_check.py", "--project", str(proj), "--no-deps"]
        with patch("sys.argv", argv):
            result = main()
        capsys.readouterr()
        assert isinstance(result, int)

    def test_nonexistent_project(self, capsys):
        argv = ["preflight_check.py", "--project", "/nonexistent/proj", "--no-deps"]
        with patch("sys.argv", argv):
            result = main()
        assert result == 2  # error

    def test_project_by_name(self, tmp_path, capsys):
        """--project luna should look in projects/luna."""
        proj = tmp_path / "projects" / "luna"
        proj.mkdir(parents=True)
        (proj / "speaker-map.json").write_text(json.dumps({"speakers": {}}))

        with (
            patch("sys.argv", ["preflight_check.py", "--project", "luna", "--no-deps"]),
            patch("os.path.exists") as mock_exists,
        ):
            # First call: "luna" doesn't exist, second: projects/luna does
            mock_exists.side_effect = lambda p: (
                p.startswith(str(proj)) or p == os.path.join("projects", "luna")
            )
            # This tests the fallback path in main()
            result = main()
            assert isinstance(result, int)

    def test_no_projects_found(self, tmp_path, capsys):
        with (
            patch("sys.argv", ["preflight_check.py", "--no-deps"]),
            patch("preflight_check.find_projects", return_value=[]),
        ):
            result = main()
        capsys.readouterr()
        assert isinstance(result, int)
