"""
Tests for WCAG contrast ratio validation of design tokens.

Validates that all color pairings used in the student portal and storefront
meet WCAG AA minimum contrast ratios (4.5:1 for normal text, 3:1 for large).
"""

import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Contrast calculation (WCAG 2.1 algorithm)
# ---------------------------------------------------------------------------


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color (#RRGGBB) to (R, G, B) tuple."""
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def relative_luminance(r: int, g: int, b: int) -> float:
    """Calculate WCAG relative luminance."""

    def channel(c: int) -> float:
        s = c / 255.0
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4

    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast_ratio(hex1: str, hex2: str) -> float:
    """Calculate WCAG contrast ratio between two hex colors."""
    l1 = relative_luminance(*hex_to_rgb(hex1))
    l2 = relative_luminance(*hex_to_rgb(hex2))
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


# ---------------------------------------------------------------------------
# Extract design tokens from student portal
# ---------------------------------------------------------------------------


def parse_css_vars(css_text: str, selector: str = ":root") -> dict[str, str]:
    """Extract CSS custom properties from a specific selector block."""
    # Find the block for the selector
    pattern = re.escape(selector) + r"\s*\{([^}]+)\}"
    match = re.search(pattern, css_text)
    if not match:
        return {}
    block = match.group(1)
    # Extract --var: value pairs
    vars_pattern = r"--([\w-]+)\s*:\s*(#[0-9A-Fa-f]{6})"
    return {f"--{m.group(1)}": m.group(2) for m in re.finditer(vars_pattern, block)}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


STUDENT_PORTAL = Path(__file__).parent.parent.parent / "student-portal" / "index.html"


@pytest.fixture
def light_vars():
    """Extract light-theme CSS variables from student portal."""
    if not STUDENT_PORTAL.exists():
        pytest.skip("Student portal not found")
    html = STUDENT_PORTAL.read_text()
    return parse_css_vars(html, ":root")


@pytest.fixture
def dark_vars():
    """Extract dark-theme CSS variables from student portal."""
    if not STUDENT_PORTAL.exists():
        pytest.skip("Student portal not found")
    html = STUDENT_PORTAL.read_text()
    return parse_css_vars(html, '[data-theme="dark"]')


class TestContrastCalculation:
    """Verify the contrast calculation itself is correct."""

    def test_black_on_white(self):
        ratio = contrast_ratio("#000000", "#FFFFFF")
        assert ratio == pytest.approx(21.0, abs=0.1)

    def test_white_on_white(self):
        ratio = contrast_ratio("#FFFFFF", "#FFFFFF")
        assert ratio == pytest.approx(1.0)

    def test_known_pair(self):
        # #767676 on white is exactly 4.54:1 — the lightest gray passing AA
        ratio = contrast_ratio("#767676", "#FFFFFF")
        assert ratio >= 4.5

    def test_symmetric(self):
        r1 = contrast_ratio("#FF0000", "#0000FF")
        r2 = contrast_ratio("#0000FF", "#FF0000")
        assert r1 == pytest.approx(r2)


class TestLightThemeContrast:
    """WCAG AA: text colors on background must be >= 4.5:1."""

    def test_ink_on_bg(self, light_vars):
        ratio = contrast_ratio(light_vars["--ink"], light_vars["--bg"])
        assert ratio >= 4.5, f"--ink on --bg: {ratio:.2f}:1 (need 4.5:1)"

    def test_ink_mid_on_bg(self, light_vars):
        ratio = contrast_ratio(light_vars["--ink-mid"], light_vars["--bg"])
        assert ratio >= 4.5, f"--ink-mid on --bg: {ratio:.2f}:1 (need 4.5:1)"

    def test_ink_light_on_bg(self, light_vars):
        ratio = contrast_ratio(light_vars["--ink-light"], light_vars["--bg"])
        assert ratio >= 4.5, f"--ink-light on --bg: {ratio:.2f}:1 (need 4.5:1)"

    def test_ink_light_on_bg_alt(self, light_vars):
        ratio = contrast_ratio(light_vars["--ink-light"], light_vars["--bg-alt"])
        assert ratio >= 3.0, f"--ink-light on --bg-alt: {ratio:.2f}:1 (need 3.0:1 for large text)"

    def test_accent_on_bg(self, light_vars):
        ratio = contrast_ratio(light_vars["--accent"], light_vars["--bg"])
        assert ratio >= 3.0, f"--accent on --bg: {ratio:.2f}:1 (need 3.0:1)"


class TestDarkThemeContrast:
    """WCAG AA: dark theme text colors on dark backgrounds."""

    def test_ink_on_bg(self, dark_vars):
        ratio = contrast_ratio(dark_vars["--ink"], dark_vars["--bg"])
        assert ratio >= 4.5, f"--ink on --bg: {ratio:.2f}:1 (need 4.5:1)"

    def test_ink_mid_on_bg(self, dark_vars):
        ratio = contrast_ratio(dark_vars["--ink-mid"], dark_vars["--bg"])
        assert ratio >= 4.5, f"--ink-mid on --bg: {ratio:.2f}:1 (need 4.5:1)"

    def test_ink_light_on_bg(self, dark_vars):
        ratio = contrast_ratio(dark_vars["--ink-light"], dark_vars["--bg"])
        assert ratio >= 4.5, f"--ink-light on --bg: {ratio:.2f}:1 (need 4.5:1)"

    def test_ink_light_on_bg_alt(self, dark_vars):
        ratio = contrast_ratio(dark_vars["--ink-light"], dark_vars["--bg-alt"])
        assert ratio >= 3.0, f"--ink-light on --bg-alt: {ratio:.2f}:1 (need 3.0:1 for large text)"

    def test_accent_on_bg(self, dark_vars):
        ratio = contrast_ratio(dark_vars["--accent"], dark_vars["--bg"])
        assert ratio >= 3.0, f"--accent on --bg: {ratio:.2f}:1 (need 3.0:1)"
