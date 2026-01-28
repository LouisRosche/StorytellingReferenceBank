#!/usr/bin/env python3
"""
Pre-flight validation for TTS pipeline.

Run this before attempting audio generation to catch issues early.
Validates: dependencies, personas, speaker maps, manuscripts, and GPU.

Usage:
    python preflight_check.py                    # Check everything
    python preflight_check.py --project luna     # Check specific project
    python preflight_check.py --deps-only        # Check only dependencies
    python preflight_check.py --fix              # Attempt auto-fixes

Exit codes:
    0: All checks passed
    1: Warnings only (can proceed)
    2: Errors found (fix before proceeding)
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))


@dataclass
class CheckResult:
    """Result of a single check."""
    name: str
    passed: bool
    message: str
    severity: str = "error"  # "error", "warning", "info"
    fix_hint: Optional[str] = None


@dataclass
class ValidationReport:
    """Full validation report."""
    checks: List[CheckResult] = field(default_factory=list)

    def add(self, result: CheckResult):
        self.checks.append(result)

    @property
    def errors(self) -> List[CheckResult]:
        return [c for c in self.checks if not c.passed and c.severity == "error"]

    @property
    def warnings(self) -> List[CheckResult]:
        return [c for c in self.checks if not c.passed and c.severity == "warning"]

    @property
    def passed(self) -> List[CheckResult]:
        return [c for c in self.checks if c.passed]

    def print_report(self):
        """Print formatted report."""
        print("\n" + "=" * 60)
        print("PRE-FLIGHT VALIDATION REPORT")
        print("=" * 60)

        # Group by category
        for check in self.checks:
            if check.passed:
                icon = "\033[92m✓\033[0m"  # Green check
            elif check.severity == "warning":
                icon = "\033[93m⚠\033[0m"  # Yellow warning
            else:
                icon = "\033[91m✗\033[0m"  # Red X

            print(f"  {icon} {check.name}: {check.message}")
            if check.fix_hint and not check.passed:
                print(f"      Fix: {check.fix_hint}")

        print("\n" + "-" * 60)
        print(f"Summary: {len(self.passed)} passed, {len(self.warnings)} warnings, {len(self.errors)} errors")

        if self.errors:
            print("\033[91mFix errors before proceeding.\033[0m")
            return 2
        elif self.warnings:
            print("\033[93mWarnings present but can proceed.\033[0m")
            return 1
        else:
            print("\033[92mAll checks passed. Ready for generation.\033[0m")
            return 0


def check_dependencies() -> List[CheckResult]:
    """Check required Python dependencies."""
    results = []

    deps = [
        ("numpy", "pip install numpy", "error"),
        ("soundfile", "pip install soundfile", "error"),
        ("scipy", "pip install scipy", "warning"),
        ("pydub", "pip install pydub", "warning"),
    ]

    for module, install_cmd, severity in deps:
        try:
            __import__(module)
            results.append(CheckResult(
                name=f"Dependency: {module}",
                passed=True,
                message="installed"
            ))
        except ImportError:
            results.append(CheckResult(
                name=f"Dependency: {module}",
                passed=False,
                message="not installed",
                severity=severity,
                fix_hint=install_cmd
            ))

    # Check PyTorch
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            gpu_name = torch.cuda.get_device_name(0)
            results.append(CheckResult(
                name="PyTorch + CUDA",
                passed=True,
                message=f"available ({gpu_name})"
            ))
        else:
            results.append(CheckResult(
                name="PyTorch + CUDA",
                passed=False,
                message="PyTorch installed but CUDA not available",
                severity="warning",
                fix_hint="Install CUDA-enabled PyTorch for GPU acceleration"
            ))
    except ImportError:
        results.append(CheckResult(
            name="PyTorch",
            passed=False,
            message="not installed",
            severity="error",
            fix_hint="pip install torch (or install via qwen-tts)"
        ))

    # Check qwen-tts
    try:
        import qwen_tts
        results.append(CheckResult(
            name="Qwen-TTS",
            passed=True,
            message="installed"
        ))
    except ImportError:
        results.append(CheckResult(
            name="Qwen-TTS",
            passed=False,
            message="not installed",
            severity="error",
            fix_hint="pip install qwen-tts"
        ))

    # Check ffmpeg (for pydub)
    import shutil
    if shutil.which("ffmpeg"):
        results.append(CheckResult(
            name="ffmpeg",
            passed=True,
            message="available"
        ))
    else:
        results.append(CheckResult(
            name="ffmpeg",
            passed=False,
            message="not found in PATH",
            severity="warning",
            fix_hint="apt install ffmpeg (Linux) or brew install ffmpeg (macOS)"
        ))

    return results


def check_project(project_path: str) -> List[CheckResult]:
    """Validate a project's structure and files."""
    results = []
    project_name = Path(project_path).name

    # Check speaker-map.json exists
    speaker_map_path = os.path.join(project_path, "speaker-map.json")
    if not os.path.exists(speaker_map_path):
        results.append(CheckResult(
            name=f"{project_name}: speaker-map.json",
            passed=False,
            message="missing",
            severity="error",
            fix_hint=f"Create {speaker_map_path}"
        ))
        return results  # Can't continue without speaker map

    results.append(CheckResult(
        name=f"{project_name}: speaker-map.json",
        passed=True,
        message="exists"
    ))

    # Load and validate speaker map
    try:
        with open(speaker_map_path) as f:
            speaker_map = json.load(f)
    except json.JSONDecodeError as e:
        results.append(CheckResult(
            name=f"{project_name}: speaker-map.json validity",
            passed=False,
            message=f"invalid JSON: {e}",
            severity="error"
        ))
        return results

    # Check default persona exists
    default_persona = speaker_map.get("default_persona", "")
    if default_persona:
        default_path = os.path.join(project_path, default_persona)
        if os.path.exists(default_path):
            results.append(CheckResult(
                name=f"{project_name}: default persona",
                passed=True,
                message=default_persona
            ))
        else:
            results.append(CheckResult(
                name=f"{project_name}: default persona",
                passed=False,
                message=f"file not found: {default_persona}",
                severity="error",
                fix_hint=f"Create {default_path}"
            ))

    # Check each speaker's persona
    speakers = speaker_map.get("speakers", {})
    for speaker, info in speakers.items():
        persona_path = info.get("persona_path")
        if persona_path:
            full_path = os.path.join(project_path, persona_path)
            if os.path.exists(full_path):
                # Validate persona JSON
                try:
                    with open(full_path) as f:
                        persona_data = json.load(f)

                    # Check required fields
                    required = ["id", "voice_prompt", "voice_attributes"]
                    missing = [r for r in required if r not in persona_data]

                    if missing:
                        results.append(CheckResult(
                            name=f"{project_name}: {speaker} persona",
                            passed=False,
                            message=f"missing fields: {missing}",
                            severity="warning"
                        ))
                    else:
                        results.append(CheckResult(
                            name=f"{project_name}: {speaker} persona",
                            passed=True,
                            message="valid"
                        ))
                except json.JSONDecodeError:
                    results.append(CheckResult(
                        name=f"{project_name}: {speaker} persona",
                        passed=False,
                        message="invalid JSON",
                        severity="error"
                    ))
            else:
                results.append(CheckResult(
                    name=f"{project_name}: {speaker} persona",
                    passed=False,
                    message=f"file not found: {persona_path}",
                    severity="error",
                    fix_hint=f"Create {full_path}"
                ))

    # Check manuscripts
    drafts_dir = os.path.join(project_path, "drafts")
    if os.path.exists(drafts_dir):
        chapters = list(Path(drafts_dir).glob("chapter-*.txt"))
        if chapters:
            results.append(CheckResult(
                name=f"{project_name}: manuscripts",
                passed=True,
                message=f"{len(chapters)} chapter(s) found"
            ))

            # Validate each chapter parses correctly
            from dialogue_parser import parse_manuscript

            for chapter in chapters:
                try:
                    with open(chapter) as f:
                        text = f.read()

                    segments, stats = parse_manuscript(text)

                    if not segments:
                        results.append(CheckResult(
                            name=f"{project_name}: {chapter.name} parsing",
                            passed=False,
                            message="no segments extracted",
                            severity="warning"
                        ))
                    else:
                        # Check for unmapped speakers
                        speaker_keys = set(k.lower() for k in speakers.keys())
                        alias_keys = set(k.lower() for k in speaker_map.get("aliases", {}).keys())
                        all_valid = speaker_keys | alias_keys | {"narrator"}

                        unmapped = set()
                        for speaker in stats.keys():
                            if speaker.lower() not in all_valid:
                                unmapped.add(speaker)

                        if unmapped:
                            results.append(CheckResult(
                                name=f"{project_name}: {chapter.name} speakers",
                                passed=False,
                                message=f"unmapped: {unmapped}",
                                severity="warning",
                                fix_hint="Add to speaker-map.json or will use default"
                            ))
                        else:
                            results.append(CheckResult(
                                name=f"{project_name}: {chapter.name}",
                                passed=True,
                                message=f"{len(segments)} segments, {len(stats)} speakers"
                            ))

                except Exception as e:
                    results.append(CheckResult(
                        name=f"{project_name}: {chapter.name}",
                        passed=False,
                        message=f"parse error: {e}",
                        severity="error"
                    ))
        else:
            results.append(CheckResult(
                name=f"{project_name}: manuscripts",
                passed=False,
                message="no chapter-*.txt files found",
                severity="warning"
            ))
    else:
        results.append(CheckResult(
            name=f"{project_name}: drafts directory",
            passed=False,
            message="missing",
            severity="warning"
        ))

    return results


def check_gpu_memory() -> List[CheckResult]:
    """Check GPU memory availability."""
    results = []

    try:
        import torch
        if torch.cuda.is_available():
            gpu_mem_total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            gpu_mem_free = (torch.cuda.get_device_properties(0).total_memory -
                          torch.cuda.memory_allocated(0)) / (1024**3)

            if gpu_mem_total >= 8:
                results.append(CheckResult(
                    name="GPU Memory",
                    passed=True,
                    message=f"{gpu_mem_total:.1f}GB total, {gpu_mem_free:.1f}GB free"
                ))
            else:
                results.append(CheckResult(
                    name="GPU Memory",
                    passed=False,
                    message=f"{gpu_mem_total:.1f}GB (recommend 8GB+ for Qwen-TTS)",
                    severity="warning"
                ))
    except Exception as e:
        results.append(CheckResult(
            name="GPU Memory",
            passed=False,
            message=f"could not check: {e}",
            severity="info"
        ))

    return results


def find_projects(base_path: str = "projects") -> List[str]:
    """Find all valid project directories."""
    projects = []

    if not os.path.exists(base_path):
        return projects

    for item in os.listdir(base_path):
        project_path = os.path.join(base_path, item)
        if os.path.isdir(project_path):
            # Must have speaker-map.json to be a valid project
            if os.path.exists(os.path.join(project_path, "speaker-map.json")):
                projects.append(project_path)

    return projects


def main():
    parser = argparse.ArgumentParser(
        description="Pre-flight validation for TTS pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument("--project", "-p", help="Check specific project only")
    parser.add_argument("--deps-only", action="store_true", help="Check dependencies only")
    parser.add_argument("--no-deps", action="store_true", help="Skip dependency checks")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    report = ValidationReport()

    # Dependency checks
    if not args.no_deps:
        print("Checking dependencies...")
        for result in check_dependencies():
            report.add(result)

    if args.deps_only:
        return report.print_report()

    # GPU memory check
    print("Checking GPU...")
    for result in check_gpu_memory():
        report.add(result)

    # Project checks
    if args.project:
        project_path = args.project
        if not os.path.exists(project_path):
            project_path = os.path.join("projects", args.project)

        if os.path.exists(project_path):
            print(f"Checking project: {project_path}")
            for result in check_project(project_path):
                report.add(result)
        else:
            report.add(CheckResult(
                name="Project",
                passed=False,
                message=f"not found: {args.project}",
                severity="error"
            ))
    else:
        projects = find_projects()
        if projects:
            print(f"Checking {len(projects)} projects...")
            for project in projects:
                for result in check_project(project):
                    report.add(result)
        else:
            report.add(CheckResult(
                name="Projects",
                passed=False,
                message="no projects found in projects/",
                severity="warning"
            ))

    return report.print_report()


if __name__ == "__main__":
    sys.exit(main())
