#!/usr/bin/env python3
"""
Validate all persona JSON files against the persona schema.

Catches: missing required fields, invalid field values, malformed JSON,
schema violations. Fast enough to run on every commit.

Usage:
    python validate_personas.py                    # Validate all personas
    python validate_personas.py --persona FILE     # Validate one file
    python validate_personas.py --json             # JSON output for CI
"""

import argparse
import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent
SCHEMA_PATH = REPO_ROOT / "personas" / "schema.json"
EXAMPLES_DIR = REPO_ROOT / "personas" / "examples"
PROJECTS_DIR = REPO_ROOT / "projects"


def load_schema():
    """Load the persona JSON schema."""
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def validate_persona(filepath, schema):
    """
    Validate a single persona JSON against the schema.

    Returns list of (severity, message) tuples. Empty list = valid.
    """
    issues = []

    # Parse JSON
    try:
        with open(filepath) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [("error", f"Invalid JSON: {e}")]

    # Required fields
    for field in schema.get("required", []):
        if field not in data:
            issues.append(("error", f"Missing required field: {field}"))

    # Field-level validation
    props = schema.get("properties", {})

    # id format
    if "id" in data:
        pattern = props.get("id", {}).get("pattern", "")
        if pattern and not re.match(pattern, data["id"]):
            issues.append(("error", f"id '{data['id']}' doesn't match pattern {pattern}"))

    # version format
    if "version" in data:
        pattern = props.get("version", {}).get("pattern", "")
        if pattern and not re.match(pattern, data["version"]):
            issues.append(("warning", f"version '{data['version']}' doesn't match semver"))

    # status enum
    if "status" in data:
        valid_statuses = props.get("status", {}).get("enum", [])
        if valid_statuses and data["status"] not in valid_statuses:
            issues.append(("error", f"Invalid status '{data['status']}', expected one of {valid_statuses}"))

    # model_variant enum
    if "model_variant" in data:
        valid_variants = props.get("model_variant", {}).get("enum", [])
        if valid_variants and data["model_variant"] not in valid_variants:
            issues.append(("warning", f"Unknown model_variant '{data['model_variant']}'"))

    # voice_prompt should be non-empty
    if "voice_prompt" in data and not data["voice_prompt"].strip():
        issues.append(("error", "voice_prompt is empty"))

    # voice_attributes checks
    attrs = data.get("voice_attributes", {})
    if attrs:
        if "languages" in attrs:
            if not isinstance(attrs["languages"], list):
                issues.append(("error", "voice_attributes.languages must be an array"))
            elif not attrs["languages"]:
                issues.append(("warning", "voice_attributes.languages is empty"))

    # emotional_range should be a list
    if "emotional_range" in data:
        if not isinstance(data["emotional_range"], list):
            issues.append(("error", "emotional_range must be an array"))
        elif not data["emotional_range"]:
            issues.append(("warning", "emotional_range is empty"))

    # use_cases should be a list
    if "use_cases" in data:
        if not isinstance(data["use_cases"], list):
            issues.append(("error", "use_cases must be an array"))
        elif not data["use_cases"]:
            issues.append(("warning", "use_cases is empty"))

    # quality.validation_status enum
    quality = data.get("quality", {})
    if quality:
        vstatus = quality.get("validation_status")
        valid_vstatus = (props.get("quality", {}).get("properties", {})
                        .get("validation_status", {}).get("enum", []))
        if vstatus and valid_vstatus and vstatus not in valid_vstatus:
            issues.append(("warning", f"Invalid validation_status '{vstatus}'"))

    # product.tier enum
    product = data.get("product", {})
    if product:
        tier = product.get("tier")
        valid_tiers = (props.get("product", {}).get("properties", {})
                      .get("tier", {}).get("enum", []))
        if tier and valid_tiers and tier not in valid_tiers:
            issues.append(("warning", f"Invalid product tier '{tier}'"))

    return issues


def find_all_personas():
    """Find all persona JSON files in the repo."""
    personas = []

    # Global examples
    if EXAMPLES_DIR.exists():
        personas.extend(EXAMPLES_DIR.glob("*.json"))

    # Project-level personas
    if PROJECTS_DIR.exists():
        for project in PROJECTS_DIR.iterdir():
            if project.is_dir():
                project_personas = project / "personas"
                if project_personas.exists():
                    personas.extend(project_personas.glob("*.json"))

    return sorted(personas)


def main():
    parser = argparse.ArgumentParser(description="Validate persona JSON files")
    parser.add_argument("--persona", "-p", help="Validate a single persona file")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    schema = load_schema()

    if args.persona:
        personas = [Path(args.persona)]
    else:
        personas = find_all_personas()

    if not personas:
        print("No persona files found.")
        return 1

    results = {}
    total_errors = 0
    total_warnings = 0

    for persona_path in personas:
        rel_path = str(persona_path.relative_to(REPO_ROOT))
        issues = validate_persona(persona_path, schema)

        errors = [msg for sev, msg in issues if sev == "error"]
        warnings = [msg for sev, msg in issues if sev == "warning"]
        total_errors += len(errors)
        total_warnings += len(warnings)

        results[rel_path] = {"errors": errors, "warnings": warnings}

        if not args.json:
            if not issues:
                print(f"  \033[92m✓\033[0m {rel_path}")
            else:
                for severity, msg in issues:
                    if severity == "error":
                        print(f"  \033[91m✗\033[0m {rel_path}: {msg}")
                    else:
                        print(f"  \033[93m⚠\033[0m {rel_path}: {msg}")

    if args.json:
        output = {
            "total_files": len(personas),
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "results": results,
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"\n{len(personas)} files checked: {total_errors} errors, {total_warnings} warnings")

    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
