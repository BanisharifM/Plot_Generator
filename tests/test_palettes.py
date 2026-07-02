"""Palette registry integrity tests."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import palettes

HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def _all_names():
    return [n for names in palettes.get_all_palette_names().values() for n in names]


def test_no_duplicate_names_across_categories():
    names = _all_names()
    assert len(names) == len(set(names)), "duplicate palette names shadow each other in get_palette"


def test_every_advertised_palette_resolves():
    for name in _all_names():
        for n in (5, 12):
            colors = palettes.get_palette(name, n)
            assert len(colors) == n, f"{name} returned {len(colors)} colors for n={n}"
            assert all(HEX.match(c) for c in colors), f"{name} returned non-hex colors"


def test_common_palettes_present():
    names = set(_all_names())
    assert {"wong", "petroff10", "tab10", "tab20", "seaborn_deep",
            "aaas", "nejm", "lancet", "jama", "cividis", "coolwarm"} <= names
