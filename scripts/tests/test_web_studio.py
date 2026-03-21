"""Tests for web_studio.py — utility functions (no Gradio dependency required)."""

import json
import sys
import types
from unittest.mock import MagicMock, patch

# Stub gradio before importing web_studio so the module loads without it.
_gr_stub = types.ModuleType("gradio")
_gr_stub.Progress = MagicMock  # type: ignore[attr-defined]
_gr_stub.Blocks = MagicMock  # type: ignore[attr-defined]
_gr_stub.themes = MagicMock()  # type: ignore[attr-defined]
sys.modules.setdefault("gradio", _gr_stub)

from web_studio import (  # noqa: E402
    _is_safe_path,
    _load_voice_prompt,
    _resolve_persona_path,
    generate_audio,
    get_manuscripts,
    get_personas,
    get_projects,
    load_manuscript,
    load_persona_details,
)

# ---------------------------------------------------------------------------
# Path safety
# ---------------------------------------------------------------------------


class TestIsSafePath:
    def test_safe_subpath(self, tmp_path):
        child = tmp_path / "sub" / "file.txt"
        child.parent.mkdir(parents=True, exist_ok=True)
        child.touch()
        assert _is_safe_path(child, tmp_path) is True

    def test_traversal_rejected(self, tmp_path):
        outside = tmp_path / ".." / "etc" / "passwd"
        assert _is_safe_path(outside, tmp_path) is False

    def test_same_directory_is_safe(self, tmp_path):
        assert _is_safe_path(tmp_path, tmp_path) is True


# ---------------------------------------------------------------------------
# get_projects / get_manuscripts / get_personas
# ---------------------------------------------------------------------------


class TestGetProjects:
    def test_returns_list(self):
        """Should return a list (possibly empty if no projects dir)."""
        result = get_projects()
        assert isinstance(result, list)

    def test_with_fake_projects_dir(self, tmp_path):
        """Should list subdirectories in projects/."""
        proj_dir = tmp_path / "projects"
        proj_dir.mkdir()
        (proj_dir / "alpha").mkdir()
        (proj_dir / "beta").mkdir()
        with patch("web_studio.PROJECT_ROOT", tmp_path):
            result = get_projects()
        assert set(result) == {"alpha", "beta"}

    def test_missing_projects_dir(self, tmp_path):
        with patch("web_studio.PROJECT_ROOT", tmp_path):
            assert get_projects() == []


class TestGetManuscripts:
    def test_returns_txt_files(self, tmp_path):
        drafts = tmp_path / "projects" / "mybook" / "drafts"
        drafts.mkdir(parents=True)
        (drafts / "chapter-01.txt").touch()
        (drafts / "chapter-02.txt").touch()
        (drafts / "notes.md").touch()  # should be excluded
        with patch("web_studio.PROJECT_ROOT", tmp_path):
            result = get_manuscripts("mybook")
        assert set(result) == {"chapter-01.txt", "chapter-02.txt"}

    def test_missing_project(self, tmp_path):
        with patch("web_studio.PROJECT_ROOT", tmp_path):
            assert get_manuscripts("nonexistent") == []


class TestGetPersonas:
    def test_finds_example_personas(self, tmp_path):
        examples = tmp_path / "personas" / "examples"
        examples.mkdir(parents=True)
        (examples / "warm-narrator.json").touch()
        with patch("web_studio.PROJECT_ROOT", tmp_path):
            result = get_personas()
        assert "examples/warm-narrator" in result

    def test_includes_project_personas(self, tmp_path):
        examples = tmp_path / "personas" / "examples"
        examples.mkdir(parents=True)
        proj_personas = tmp_path / "projects" / "book1" / "personas"
        proj_personas.mkdir(parents=True)
        (proj_personas / "hero.json").touch()
        with patch("web_studio.PROJECT_ROOT", tmp_path):
            result = get_personas("book1")
        assert "book1/hero" in result


# ---------------------------------------------------------------------------
# load_manuscript / load_persona_details
# ---------------------------------------------------------------------------


class TestLoadManuscript:
    def test_loads_text(self, tmp_path):
        drafts = tmp_path / "projects" / "demo" / "drafts"
        drafts.mkdir(parents=True)
        ms = drafts / "ch1.txt"
        ms.write_text("Once upon a time...")
        with patch("web_studio.PROJECT_ROOT", tmp_path):
            assert load_manuscript("demo", "ch1.txt") == "Once upon a time..."

    def test_missing_file(self, tmp_path):
        with patch("web_studio.PROJECT_ROOT", tmp_path):
            assert load_manuscript("noproject", "nofile.txt") == ""

    def test_traversal_returns_empty(self, tmp_path):
        with patch("web_studio.PROJECT_ROOT", tmp_path):
            assert load_manuscript("../../etc", "passwd") == ""


class TestLoadPersonaDetails:
    def test_loads_json(self, tmp_path):
        examples = tmp_path / "personas" / "examples"
        examples.mkdir(parents=True)
        persona = examples / "narrator.json"
        persona.write_text('{"id": "narrator"}')
        with patch("web_studio.PROJECT_ROOT", tmp_path):
            result = load_persona_details("examples/narrator")
        assert json.loads(result)["id"] == "narrator"

    def test_missing_returns_empty_json(self, tmp_path):
        with patch("web_studio.PROJECT_ROOT", tmp_path):
            assert load_persona_details("examples/missing") == "{}"


# ---------------------------------------------------------------------------
# _resolve_persona_path / _load_voice_prompt
# ---------------------------------------------------------------------------


class TestResolvePersonaPath:
    def test_example_persona(self, tmp_path):
        with patch("web_studio.PROJECT_ROOT", tmp_path):
            result = _resolve_persona_path("examples/narrator")
        assert result is not None
        assert "personas/examples/narrator.json" in str(result)

    def test_project_persona(self, tmp_path):
        with patch("web_studio.PROJECT_ROOT", tmp_path):
            result = _resolve_persona_path("mybook/hero")
        assert result is not None
        assert "projects/mybook/personas/hero.json" in str(result)

    def test_empty_returns_none(self):
        assert _resolve_persona_path("") is None
        assert _resolve_persona_path(None) is None


class TestLoadVoicePrompt:
    def test_loads_prompt(self, tmp_path):
        persona_file = tmp_path / "persona.json"
        persona_file.write_text(json.dumps({"voice_prompt": "Speak warmly"}))
        assert _load_voice_prompt(persona_file) == "Speak warmly"

    def test_missing_key(self, tmp_path):
        persona_file = tmp_path / "persona.json"
        persona_file.write_text(json.dumps({"id": "test"}))
        assert _load_voice_prompt(persona_file) == ""

    def test_missing_file(self, tmp_path):
        assert _load_voice_prompt(tmp_path / "nonexistent.json") == ""

    def test_none_path(self):
        assert _load_voice_prompt(None) == ""


# ---------------------------------------------------------------------------
# generate_audio (with TTS mocked out)
# ---------------------------------------------------------------------------


class TestGenerateAudio:
    def test_empty_text_returns_none(self):
        result, msg = generate_audio("", "examples/test", "qwen")
        assert result is None
        assert "No text" in msg

    def test_whitespace_text_returns_none(self):
        result, msg = generate_audio("   ", "examples/test", "qwen")
        assert result is None
        assert "No text" in msg

    def test_no_tts_available(self):
        with patch("web_studio._TTS_AVAILABLE", False):
            result, msg = generate_audio("Hello world", "examples/test", "qwen")
        assert result is None
        assert "not available" in msg
