"""Per-chart palette defaults and the no-interpolated-qualitative rule."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config.palettes import HEATMAP_PALETTES, default_palette
from core.base_plotter import PlotConfig
from plotters.statistical.heatmap import HeatmapPlotter


def test_single_series_default_leads_with_okabe_ito_blue():
    for pid in ("temporal.line", "statistical.histogram", "categorical.bar"):
        assert default_palette(pid)[0] == "#0072B2"


def _heatmap(palette):
    rng = np.random.default_rng(0)
    df = pd.DataFrame(rng.normal(size=(50, 3)), columns=list("abc"))
    cfg = PlotConfig()
    cfg.color_palette = palette
    p = HeatmapPlotter(df, cfg)
    p.set_columns(list("abc"))
    p.set_heatmap_params(correlation=True)
    fig, ax = p.plot()
    name = ax.get_images()[0].get_cmap().name
    plt.close(fig)
    return name


def test_qualitative_palette_never_interpolated_on_heatmap():
    assert _heatmap(["#ff0000", "#00ff00", "#0000ff"]) == "RdBu_r"


def test_continuous_palette_still_honored_on_heatmap():
    assert _heatmap(list(HEATMAP_PALETTES["viridis"])) == "custom"
