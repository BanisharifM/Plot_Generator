"""Spec save/load round-trip."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.base_plotter import PlotConfig
from core.spec import apply_spec, build_spec


def test_round_trip():
    session = {"plot_config": PlotConfig(), "cfg_width": 3.5, "cfg_dpi": 300,
               "style_preset": "IEEE"}
    session["plot_config"].color_palette = ["#ff0000"]
    text = build_spec(session, "temporal.line",
                      {"x_column": "t", "y_columns": ["v"]})
    spec = json.loads(text)

    fresh = {"plot_config": PlotConfig()}
    apply_spec(fresh, spec)
    assert fresh["sel_category"] == "temporal" and fresh["sel_plot"] == "line"
    assert fresh["sb_temporal.line_x_column"] == "t"
    assert fresh["ms_temporal.line_y_columns"] == ["v"]
    assert fresh["cfg_width"] == 3.5
    assert fresh["plot_config"].color_palette == ["#ff0000"]
