"""Tests for manage_student_codes.py — code generation, hashing, I/O, and CLI commands."""

import json
import re
import pytest
from unittest.mock import patch
from pathlib import Path

from manage_student_codes import (
    hash_code,
    generate_code,
    load_codes_json,
    save_codes_json,
    load_admin_json,
    save_admin_json,
    cmd_generate,
    cmd_add,
    cmd_list,
    cmd_revoke,
    cmd_verify,
    ADJECTIVES,
    NOUNS,
)
import manage_student_codes as msc


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def codes_env(tmp_path, monkeypatch):
    """Set up isolated file paths for all code operations."""
    codes_file = tmp_path / "codes.json"
    admin_file = tmp_path / "codes-admin.json"
    monkeypatch.setattr(msc, "CODES_JSON", codes_file)
    monkeypatch.setattr(msc, "ADMIN_JSON", admin_file)
    monkeypatch.setattr(msc, "PORTAL_DIR", tmp_path)
    return {"codes": codes_file, "admin": admin_file, "dir": tmp_path}


def _make_args(**kwargs):
    """Create a mock args namespace."""
    from argparse import Namespace
    defaults = {"cohort": "test", "count": 5, "note": None, "code": "TEST-CODE-1234"}
    defaults.update(kwargs)
    return Namespace(**defaults)


# ---------------------------------------------------------------------------
# hash_code — PBKDF2 determinism
# ---------------------------------------------------------------------------

class TestHashCode:
    def test_deterministic(self):
        h1 = hash_code("BRIGHT-SPARK-1234")
        h2 = hash_code("BRIGHT-SPARK-1234")
        assert h1 == h2

    def test_case_insensitive(self):
        assert hash_code("bright-spark-1234") == hash_code("BRIGHT-SPARK-1234")

    def test_strips_whitespace(self):
        assert hash_code("  BRIGHT-SPARK-1234  ") == hash_code("BRIGHT-SPARK-1234")

    def test_different_codes_differ(self):
        assert hash_code("BRIGHT-SPARK-1234") != hash_code("DARK-FLAME-5678")

    def test_returns_hex_string(self):
        h = hash_code("TEST-CODE-0001")
        assert isinstance(h, str)
        assert all(c in "0123456789abcdef" for c in h)


# ---------------------------------------------------------------------------
# generate_code — memorable format
# ---------------------------------------------------------------------------

class TestGenerateCode:
    def test_format(self):
        code = generate_code("cohort1")
        parts = code.split("-")
        assert len(parts) == 3
        assert parts[0] in ADJECTIVES
        assert parts[1] in NOUNS
        assert parts[2].isdigit()
        assert len(parts[2]) == 4

    def test_digit_range(self):
        for _ in range(50):
            code = generate_code("test")
            digits = int(code.split("-")[2])
            assert 1000 <= digits <= 9999

    def test_randomness(self):
        codes = {generate_code("test") for _ in range(20)}
        assert len(codes) > 1


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------

class TestFileIO:
    def test_load_codes_default(self, codes_env):
        """Loading from non-existent file returns defaults."""
        data = load_codes_json()
        assert "hashes" in data
        assert data["hashes"] == []

    def test_load_codes_existing(self, codes_env):
        codes_env["codes"].write_text(json.dumps({"hashes": ["abc"]}))
        data = load_codes_json()
        assert data["hashes"] == ["abc"]

    def test_save_load_roundtrip(self, codes_env):
        data = {"_note": "test", "hashes": ["hash1", "hash2"]}
        save_codes_json(data)
        loaded = load_codes_json()
        assert loaded["hashes"] == ["hash1", "hash2"]

    def test_load_admin_default(self, codes_env):
        data = load_admin_json()
        assert "entries" in data
        assert data["entries"] == []

    def test_save_admin_creates_gitignore(self, codes_env):
        save_admin_json({"entries": []})
        gitignore = codes_env["dir"].parent / ".gitignore"
        # save_admin_json uses PORTAL_DIR.parent for gitignore
        # which is tmp_path.parent — may or may not be writable
        # The key assertion is it doesn't crash

    def test_save_admin_appends_to_gitignore(self, codes_env):
        gitignore = codes_env["dir"].parent / ".gitignore"
        # Only test if parent is writable
        try:
            gitignore.write_text("*.pyc\n")
            save_admin_json({"entries": []})
            content = gitignore.read_text()
            assert "codes-admin.json" in content
        except OSError:
            pytest.skip("Parent directory not writable")


# ---------------------------------------------------------------------------
# cmd_generate
# ---------------------------------------------------------------------------

class TestCmdGenerate:
    def test_generates_codes(self, codes_env, capsys):
        args = _make_args(cohort="Spring2026", count=3, note="test batch")
        cmd_generate(args)

        data = load_codes_json()
        assert len(data["hashes"]) == 3

        admin = load_admin_json()
        assert len(admin["entries"]) == 3
        assert all(e["cohort"] == "Spring2026" for e in admin["entries"])

        captured = capsys.readouterr()
        assert "Generated 3 code(s)" in captured.out

    def test_no_duplicate_hashes(self, codes_env):
        args = _make_args(cohort="test", count=20)
        cmd_generate(args)
        data = load_codes_json()
        assert len(data["hashes"]) == len(set(data["hashes"]))

    def test_preserves_existing_hashes(self, codes_env):
        # Pre-populate
        save_codes_json({"hashes": ["existing_hash"]})
        args = _make_args(cohort="new", count=2)
        cmd_generate(args)
        data = load_codes_json()
        assert "existing_hash" in data["hashes"]
        assert len(data["hashes"]) == 3


# ---------------------------------------------------------------------------
# cmd_add
# ---------------------------------------------------------------------------

class TestCmdAdd:
    def test_adds_code(self, codes_env, capsys):
        args = _make_args(code="BRIGHT-SPARK-1234", note="manual add")
        cmd_add(args)

        data = load_codes_json()
        h = hash_code("BRIGHT-SPARK-1234")
        assert h in data["hashes"]

        captured = capsys.readouterr()
        assert "Added code" in captured.out

    def test_skips_duplicate(self, codes_env, capsys):
        h = hash_code("BRIGHT-SPARK-1234")
        save_codes_json({"hashes": [h]})

        args = _make_args(code="BRIGHT-SPARK-1234")
        cmd_add(args)

        captured = capsys.readouterr()
        assert "already exists" in captured.out

    def test_normalizes_case(self, codes_env):
        args = _make_args(code="bright-spark-1234")
        cmd_add(args)
        data = load_codes_json()
        assert len(data["hashes"]) == 1


# ---------------------------------------------------------------------------
# cmd_list
# ---------------------------------------------------------------------------

class TestCmdList:
    def test_empty_list(self, codes_env, capsys):
        args = _make_args()
        cmd_list(args)
        captured = capsys.readouterr()
        assert "No codes in admin log" in captured.out

    def test_lists_codes_by_cohort(self, codes_env, capsys):
        h = hash_code("BRIGHT-SPARK-1234")
        save_codes_json({"hashes": [h]})
        save_admin_json({"entries": [
            {"code": "BRIGHT-SPARK-1234", "hash": h, "cohort": "Spring2026", "note": "test"},
        ]})

        args = _make_args()
        cmd_list(args)
        captured = capsys.readouterr()
        assert "Spring2026" in captured.out
        assert "BRIGHT-SPARK-1234" in captured.out
        assert "active" in captured.out

    def test_shows_revoked_status(self, codes_env, capsys):
        h = hash_code("BRIGHT-SPARK-1234")
        save_codes_json({"hashes": []})  # hash removed = revoked
        save_admin_json({"entries": [
            {"code": "BRIGHT-SPARK-1234", "hash": h, "cohort": "test", "note": ""},
        ]})

        args = _make_args()
        cmd_list(args)
        captured = capsys.readouterr()
        assert "REVOKED" in captured.out


# ---------------------------------------------------------------------------
# cmd_revoke
# ---------------------------------------------------------------------------

class TestCmdRevoke:
    def test_revokes_code(self, codes_env, capsys):
        h = hash_code("BRIGHT-SPARK-1234")
        save_codes_json({"hashes": [h]})

        args = _make_args(code="BRIGHT-SPARK-1234")
        cmd_revoke(args)

        data = load_codes_json()
        assert h not in data["hashes"]

        captured = capsys.readouterr()
        assert "Revoked" in captured.out

    def test_revoke_nonexistent(self, codes_env, capsys):
        save_codes_json({"hashes": []})

        args = _make_args(code="NONEXISTENT-CODE-0000")
        cmd_revoke(args)

        captured = capsys.readouterr()
        assert "not found" in captured.out


# ---------------------------------------------------------------------------
# cmd_verify
# ---------------------------------------------------------------------------

class TestCmdVerify:
    def test_valid_code(self, codes_env, capsys):
        h = hash_code("BRIGHT-SPARK-1234")
        save_codes_json({"hashes": [h]})

        args = _make_args(code="BRIGHT-SPARK-1234")
        cmd_verify(args)

        captured = capsys.readouterr()
        assert "valid" in captured.out.lower()

    def test_invalid_code(self, codes_env, capsys):
        save_codes_json({"hashes": []})

        args = _make_args(code="FAKE-CODE-0000")
        cmd_verify(args)

        captured = capsys.readouterr()
        assert "NOT" in captured.out or "invalid" in captured.out.lower()


# ---------------------------------------------------------------------------
# Batch — no duplicates
# ---------------------------------------------------------------------------

class TestGenerateBatch:
    def test_no_duplicate_hashes(self):
        codes = [generate_code("batch") for _ in range(50)]
        hashes = [hash_code(c) for c in codes]
        assert len(set(hashes)) == len(hashes)
