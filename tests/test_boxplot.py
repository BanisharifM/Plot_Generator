"""Regression test for the Box Plot crash on matplotlib >= 3.11 (ROADMAP 0.1).

matplotlib 3.9 renamed ax.boxplot(labels=...) to tick_labels= and removed
labels= in 3.11; vert= is deprecated in favor of orientation=.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from core.base_plotter import PlotConfig
from plotters.statistical.boxplot import BoxPlotter


@pytest.fixture
def df():
    rng = np.random.default_rng(0)
    return pd.DataFrame({
        "temperature": rng.normal(20, 5, 200),
        "pressure": rng.normal(1013, 8, 200),
        "region": rng.choice(["north", "south"], 200),
    })


def test_boxplot_multiple_columns(df):
    plotter = BoxPlotter(df, PlotConfig())
    plotter.set_columns(["temperature", "pressure"])
    fig, ax = plotter.plot()
    tick_labels = [t.get_text() for t in ax.get_xticklabels()]
    assert tick_labels == ["temperature", "pressure"]
    plt.close(fig)


def test_boxplot_grouped(df):
    plotter = BoxPlotter(df, PlotConfig())
    plotter.set_columns(["temperature"], group_column="region")
    fig, ax = plotter.plot()
    assert len(ax.get_xticklabels()) == 2  # one box per region
    plt.close(fig)


def test_boxplot_horizontal(df):
    plotter = BoxPlotter(df, PlotConfig())
    plotter.set_columns(["temperature"])
    plotter.set_box_params(orientation="horizontal")
    fig, ax = plotter.plot()
    assert [t.get_text() for t in ax.get_yticklabels()] == ["temperature"]
    plt.close(fig)
