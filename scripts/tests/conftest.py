"""Pytest configuration — adds scripts/ to sys.path for test discovery."""

import sys
from pathlib import Path

# __file__ is scripts/tests/conftest.py → parent.parent is scripts/
sys.path.insert(0, str(Path(__file__).parent.parent))
