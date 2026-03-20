#!/usr/bin/env python3
"""
WCAG contrast ratio validator for CSS custom property themes.

Parses an HTML file for :root and [data-theme="dark"] CSS variable blocks,
then checks that text/background color pairings meet WCAG AA minimums.

Usage:
    python check_contrast.py student-portal/index.html
"""

import re
import sys
from pathlib import Path


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def relative_luminance(r: int, g: int, b: int) -> float:
    def channel(c: int) -> float:
        s = c / 255.0
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4

    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast_ratio(c1: str, c2: str) -> float:
    l1 = relative_luminance(*hex_to_rgb(c1))
    l2 = relative_luminance(*hex_to_rgb(c2))
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def parse_css_vars(css: str, selector: str) -> dict[str, str]:
    pattern = re.escape(selector) + r"\s*\{([^}]+)\}"
    m = re.search(pattern, css)
    if not m:
        return {}
    return {
        f"--{g.group(1)}": g.group(2)
        for g in re.finditer(r"--([\w-]+)\s*:\s*(#[0-9A-Fa-f]{6})", m.group(1))
    }


# Pairings to check: (foreground var, background var, minimum ratio)
CHECKS = [
    ("--ink", "--bg", 4.5),
    ("--ink-mid", "--bg", 4.5),
    ("--ink-light", "--bg", 4.5),
    ("--accent", "--bg", 3.0),
]


def main() -> int:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <html-file>", file=sys.stderr)
        return 1

    html_path = Path(sys.argv[1])
    if not html_path.exists():
        print(f"File not found: {html_path}", file=sys.stderr)
        return 1

    html = html_path.read_text()
    themes = [
        ("light", ":root"),
        ("dark", '[data-theme="dark"]'),
    ]

    failures = []
    for theme_name, selector in themes:
        variables = parse_css_vars(html, selector)
        if not variables:
            print(f"Warning: no CSS variables found for {selector}")
            continue

        for fg_var, bg_var, min_ratio in CHECKS:
            fg = variables.get(fg_var)
            bg = variables.get(bg_var)
            if not fg or not bg:
                continue
            ratio = contrast_ratio(fg, bg)
            status = "PASS" if ratio >= min_ratio else "FAIL"
            print(f"  {status}: {theme_name} {fg_var} ({fg}) on {bg_var} ({bg}) = {ratio:.2f}:1 (need {min_ratio}:1)")
            if ratio < min_ratio:
                failures.append(f"{theme_name} {fg_var} on {bg_var}")

    if failures:
        print(f"\n{len(failures)} contrast failure(s) — fix before merging.")
        return 1

    print("\nAll WCAG contrast ratios pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
