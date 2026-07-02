"""Generate a runnable Python script that reproduces the current figure.

The script references the data FILE (never inlines rows, so it works at
2M+ samples), re-runs the same DuckDB reduction the app used, and applies
the full styling. Run it from the repo root: python repro_chart.py
"""

import json

_TEMPLATE = '''#!/usr/bin/env python3
"""Reproduces a {plot_id} chart made with Publication Plot Generator.

Run from the Plot_Generator repo root:  python {script_name}
Data file: {data_path}
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import matplotlib
matplotlib.use("Agg")

from core.base_plotter import PlotConfig
from core.data_source import DataSource
from core.reductions import reduce_for_plot
from core.plot_registry import plot_registry
from utils.data_loader import DataLoader
import plotters  # noqa: F401  (registers plot types)

SPEC = {spec}

source = DataSource(r"{data_path}")
df, note = reduce_for_plot(source, SPEC["plot_id"], SPEC["params"])
df = DataLoader._infer_datetimes(df)
if note:
    print(f"reduction: {{note}}")

config = PlotConfig(**{{k: tuple(v) if k == "figsize" else v
                       for k, v in SPEC["config"].items()}})
plotter = plot_registry.create_plot(SPEC["plot_id"], df, config)

p = SPEC["params"]
if "x_column" in p and "y_columns" in p:
    plotter.set_columns(p["x_column"], p["y_columns"])
elif "x_column" in p and "y_column" in p:
    plotter.set_columns(p["x_column"], p["y_column"])
elif "value_column" in p:
    plotter.set_columns(p["value_column"], p.get("group_column"))
elif "value_columns" in p:
    plotter.set_columns(p["value_columns"])

fig, ax = plotter.plot()
out = Path("{out_name}")
fig.savefig(out, dpi=config.dpi, bbox_inches="tight")
print(f"wrote {{out.resolve()}}")
'''


def generate_script(spec_json: str, data_path: str,
                    script_name: str = "repro_chart.py") -> str:
    spec = json.loads(spec_json)
    plot_id = spec["plot_id"]
    return _TEMPLATE.format(
        plot_id=plot_id,
        script_name=script_name,
        data_path=data_path,
        # repr() emits valid Python literals (True/None), unlike JSON text
        spec=repr({k: spec[k] for k in ("plot_id", "params", "config")}),
        out_name=plot_id.replace(".", "_") + ".png",
    )
