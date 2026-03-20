"""Tests for manage_student_codes.py — code generation, hashing, I/O."""

import json
import re
import pytest
from unittest.mock import patch
from pathlib import Path

from manage_student_codes import (
    hash_code,
    generate_code,
    ADJECTIVES,
    NOUNS,
)


# ---------------------------------------------------------------------------
# hash_code — PBKDF2 determinism
# ---------------------------------------------------------------------------

class TestHashCode:
    def test_deterministic(self):
        """Same input always produces the same hash."""
        h1 = hash_code("BRIGHT-SPARK-1234")
        h2 = hash_code("BRIGHT-SPARK-1234")
        assert h1 == h2

    def test_case_insensitive(self):
        """Hashing normalizes to uppercase."""
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
        """Digits should be 1000–9999."""
        for _ in range(50):
            code = generate_code("test")
            digits = int(code.split("-")[2])
            assert 1000 <= digits <= 9999

    def test_randomness(self):
        """Multiple calls should (almost certainly) produce different codes."""
        codes = {generate_code("test") for _ in range(20)}
        assert len(codes) > 1


# ---------------------------------------------------------------------------
# generate_codes — batch with no duplicates (via cmd_generate)
# ---------------------------------------------------------------------------

class TestGenerateBatch:
    def test_no_duplicate_hashes(self):
        """Generating many codes should produce unique hashes."""
        codes = [generate_code("batch") for _ in range(50)]
        hashes = [hash_code(c) for c in codes]
        assert len(set(hashes)) == len(hashes)


# ---------------------------------------------------------------------------
# File I/O — save and load round-trip
# ---------------------------------------------------------------------------

class TestFileIO:
    def test_codes_round_trip(self, tmp_path):
        """codes.json round-trips correctly."""
        codes_file = tmp_path / "codes.json"
        data = {"_note": "test", "hashes": ["aaa", "bbb"]}
        codes_file.write_text(json.dumps(data, indent=2))

        loaded = json.loads(codes_file.read_text())
        assert loaded["hashes"] == ["aaa", "bbb"]

    def test_admin_round_trip(self, tmp_path):
        """codes-admin.json round-trips with entries."""
        admin_file = tmp_path / "codes-admin.json"
        entry = {"code": "BRIGHT-SPARK-1234", "hash": "abc123", "cohort": "test", "note": ""}
        data = {"_note": "admin", "entries": [entry]}
        admin_file.write_text(json.dumps(data, indent=2))

        loaded = json.loads(admin_file.read_text())
        assert len(loaded["entries"]) == 1
        assert loaded["entries"][0]["code"] == "BRIGHT-SPARK-1234"

    def test_save_and_load_integration(self, tmp_path, monkeypatch):
        """End-to-end: save codes, load them, verify hash lookup works."""
        import manage_student_codes as msc

        codes_file = tmp_path / "codes.json"
        admin_file = tmp_path / "codes-admin.json"
        monkeypatch.setattr(msc, "CODES_JSON", codes_file)
        monkeypatch.setattr(msc, "ADMIN_JSON", admin_file)
        # Prevent .gitignore writes
        monkeypatch.setattr(msc, "PORTAL_DIR", tmp_path)

        # Start fresh
        code = generate_code("integration")
        h = hash_code(code)

        codes_data = msc.load_codes_json()
        codes_data["hashes"].append(h)
        msc.save_codes_json(codes_data)

        admin_data = msc.load_admin_json()
        admin_data["entries"].append({"code": code, "hash": h, "cohort": "test", "note": ""})
        msc.save_admin_json(admin_data)

        # Reload and verify
        reloaded = msc.load_codes_json()
        assert h in reloaded["hashes"]
