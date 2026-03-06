#!/usr/bin/env python3
"""
manage_student_codes.py — Admin tool for student library access codes.

Usage:
  python scripts/manage_student_codes.py generate <cohort> [--count N]
  python scripts/manage_student_codes.py list
  python scripts/manage_student_codes.py add <code> [--note "..."]
  python scripts/manage_student_codes.py revoke <code>
  python scripts/manage_student_codes.py verify <code>

Files:
  student-portal/codes.json      — hashes only (served to browser)
  student-portal/codes-admin.json — full mapping with labels (DO NOT commit)
"""

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

PORTAL_DIR   = Path(__file__).parent.parent / "student-portal"
CODES_JSON   = PORTAL_DIR / "codes.json"
ADMIN_JSON   = PORTAL_DIR / "codes-admin.json"

# Word lists for memorable code generation
ADJECTIVES = [
    "AMBER", "BRIGHT", "CLEAR", "DARK", "EMBER", "FAINT",
    "GOLD", "HARSH", "INNER", "KEEN", "LIGHT", "MUTED",
    "NIGHT", "OPEN", "PLAIN", "QUIET", "RARE", "SHARP",
    "STILL", "TRUE", "VIVID", "WARM", "WILD", "YOUNG",
]
NOUNS = [
    "CRAFT", "DRAFT", "FLAME", "GLOOM", "HOOK", "INK",
    "LEAP", "MIND", "NOTE", "PAGE", "PULSE", "QUEST",
    "RIFT", "SCENE", "SPARK", "STAGE", "TALE", "THREAD",
    "TIDE", "TONE", "VERSE", "VOICE", "WORD", "WORLD",
]


# ─────────────────────────────────────────────
# Hash / code utilities
# ─────────────────────────────────────────────

def hash_code(code: str) -> str:
    normalized = code.strip().upper()
    return hashlib.sha256(normalized.encode()).hexdigest()


def generate_code(cohort: str, suffix_len: int = 4) -> str:
    adj  = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    digits = str(random.randint(1000, 9999))
    return f"{adj}-{noun}-{digits}"


def load_codes_json() -> dict:
    if CODES_JSON.exists():
        return json.loads(CODES_JSON.read_text())
    return {"_note": "SHA-256 hashes of valid access codes. Manage via scripts/manage_student_codes.py", "hashes": []}


def save_codes_json(data: dict) -> None:
    CODES_JSON.write_text(json.dumps(data, indent=2))


def load_admin_json() -> dict:
    if ADMIN_JSON.exists():
        return json.loads(ADMIN_JSON.read_text())
    return {"_note": "ADMIN ONLY — do not commit this file. Maps plaintext codes to hashes.", "entries": []}


def save_admin_json(data: dict) -> None:
    ADMIN_JSON.write_text(json.dumps(data, indent=2))
    # Remind operator to gitignore
    gitignore = PORTAL_DIR.parent / ".gitignore"
    ignore_line = "student-portal/codes-admin.json"
    if gitignore.exists():
        content = gitignore.read_text()
        if ignore_line not in content:
            gitignore.write_text(content.rstrip() + f"\n{ignore_line}\n")
            print(f"  [info] Added {ignore_line} to .gitignore")
    else:
        gitignore.write_text(f"{ignore_line}\n")
        print(f"  [info] Created .gitignore with {ignore_line}")


# ─────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────

def cmd_generate(args) -> None:
    cohort = args.cohort
    count  = args.count

    codes_data = load_codes_json()
    admin_data = load_admin_json()
    existing_hashes = set(codes_data["hashes"])

    new_codes = []
    attempts = 0
    while len(new_codes) < count and attempts < count * 10:
        attempts += 1
        code = generate_code(cohort)
        h    = hash_code(code)
        if h not in existing_hashes:
            existing_hashes.add(h)
            new_codes.append({"code": code, "hash": h, "cohort": cohort, "note": args.note or ""})

    # Persist
    codes_data["hashes"] = list(existing_hashes)
    admin_data["entries"].extend(new_codes)
    save_codes_json(codes_data)
    save_admin_json(admin_data)

    print(f"\nGenerated {len(new_codes)} code(s) for cohort '{cohort}':\n")
    for entry in new_codes:
        print(f"  {entry['code']}")
    print(f"\ncodes.json updated ({len(codes_data['hashes'])} total hashes).")
    print("codes-admin.json updated (keep private — do not commit).\n")


def cmd_add(args) -> None:
    code = args.code.strip().upper()
    h    = hash_code(code)

    codes_data = load_codes_json()
    admin_data = load_admin_json()

    if h in codes_data["hashes"]:
        print(f"  [skip] Code '{code}' already exists.")
        return

    codes_data["hashes"].append(h)
    admin_data["entries"].append({"code": code, "hash": h, "cohort": "", "note": args.note or ""})
    save_codes_json(codes_data)
    save_admin_json(admin_data)

    print(f"  [ok] Added code: {code}")
    print(f"       Hash: {h}")


def cmd_list(args) -> None:
    admin_data = load_admin_json()
    codes_data = load_codes_json()
    active_hashes = set(codes_data["hashes"])

    entries = admin_data.get("entries", [])
    if not entries:
        print("No codes in admin log. (codes.json may have hashes added manually.)")
        print(f"Total hashes in codes.json: {len(codes_data['hashes'])}")
        return

    by_cohort: dict[str, list] = {}
    for e in entries:
        cohort = e.get("cohort") or "—"
        by_cohort.setdefault(cohort, []).append(e)

    print()
    for cohort, items in sorted(by_cohort.items()):
        print(f"  Cohort: {cohort}")
        for e in items:
            status = "active" if e["hash"] in active_hashes else "REVOKED"
            note   = f"  [{e['note']}]" if e.get("note") else ""
            print(f"    {e['code']:<28}  {status}{note}")
        print()

    print(f"Total active hashes in codes.json: {len(codes_data['hashes'])}")
    orphan = len(active_hashes) - sum(
        1 for e in entries if e["hash"] in active_hashes
    )
    if orphan > 0:
        print(f"  (+{orphan} hashes in codes.json not tracked in admin log)")
    print()


def cmd_revoke(args) -> None:
    code = args.code.strip().upper()
    h    = hash_code(code)

    codes_data = load_codes_json()
    if h not in codes_data["hashes"]:
        print(f"  [skip] Hash for '{code}' not found in codes.json (already revoked or never added).")
        return

    codes_data["hashes"].remove(h)
    save_codes_json(codes_data)
    print(f"  [ok] Revoked code: {code}")
    print(f"       codes.json now has {len(codes_data['hashes'])} hashes.")


def cmd_verify(args) -> None:
    code = args.code.strip().upper()
    h    = hash_code(code)
    codes_data = load_codes_json()

    if h in codes_data["hashes"]:
        print(f"  [valid] '{code}' is a recognized access code.")
    else:
        print(f"  [invalid] '{code}' is NOT in codes.json.")


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Manage student library access codes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # generate
    p_gen = sub.add_parser("generate", help="Generate N random codes for a cohort")
    p_gen.add_argument("cohort", help="Cohort label (e.g. 'Spring2026-Period3')")
    p_gen.add_argument("--count", "-n", type=int, default=30, help="Number of codes (default: 30)")
    p_gen.add_argument("--note", help="Optional note attached to all generated codes")
    p_gen.set_defaults(func=cmd_generate)

    # add
    p_add = sub.add_parser("add", help="Add a specific code manually")
    p_add.add_argument("code", help="The plaintext access code")
    p_add.add_argument("--note", help="Optional note")
    p_add.set_defaults(func=cmd_add)

    # list
    p_list = sub.add_parser("list", help="List all codes from the admin log")
    p_list.set_defaults(func=cmd_list)

    # revoke
    p_rev = sub.add_parser("revoke", help="Revoke a specific code")
    p_rev.add_argument("code", help="The plaintext access code to revoke")
    p_rev.set_defaults(func=cmd_revoke)

    # verify
    p_ver = sub.add_parser("verify", help="Check if a code is currently valid")
    p_ver.add_argument("code", help="The plaintext code to check")
    p_ver.set_defaults(func=cmd_verify)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
