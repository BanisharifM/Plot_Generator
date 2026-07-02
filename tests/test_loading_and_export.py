"""Tests for load-time dtype inference and export filename sanitization."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from config import settings
from core.exporters import PlotExporter
from utils.data_loader import DataLoader


def _write_csv(tmp_path):
    p = tmp_path / "d.csv"
    pd.DataFrame({
        "date": pd.date_range("2023-01-01", periods=40).strftime("%Y-%m-%d"),
        "category": ["a", "b"] * 20,
        "zip": ["02139", "94105"] * 20,   # numeric-looking strings, not dates
        "value": range(40),
    }).to_csv(p, index=False)
    return p


def test_dates_inferred_others_untouched(tmp_path):
    df = DataLoader.load_file(str(_write_csv(tmp_path)))
    assert pd.api.types.is_datetime64_any_dtype(df["date"])
    assert not pd.api.types.is_datetime64_any_dtype(df["category"])
    assert not pd.api.types.is_datetime64_any_dtype(df["zip"])
    assert df["date"].is_monotonic_increasing


def test_export_filename_cannot_escape_exports_dir():
    fig, ax = plt.subplots()
    ax.plot([1, 2], [1, 2])
    for evil in ["../../evil", "/tmp/abs", "a/b/../c"]:
        path = PlotExporter.export(fig, evil, format="png", dpi=72)
        assert path.parent == settings.EXPORTS_DIR
        assert ".." not in path.name and "/" not in path.name
        path.unlink()
    plt.close(fig)
