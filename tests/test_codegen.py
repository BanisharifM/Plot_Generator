"""The exported script must actually run and produce the figure file."""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd

from core.base_plotter import PlotConfig
from core.codegen import generate_script
from core.spec import build_spec

ROOT = Path(__file__).parent.parent


def test_exported_script_reproduces_figure(tmp_path):
    rng = np.random.default_rng(0)
    data = tmp_path / "d.csv"
    pd.DataFrame({"cat": rng.choice(list("AB"), 300),
                  "v": rng.normal(10, 2, 300)}).to_csv(data, index=False)

    session = {"plot_config": PlotConfig()}
    spec = build_spec(session, "categorical.bar",
                      {"x_column": "cat", "y_columns": ["v"]})
    script = tmp_path / "repro.py"
    script.write_text(generate_script(spec, str(data), script.name))

    # the script inserts its own dir on sys.path; run it from the repo root
    run = subprocess.run([sys.executable, str(script)], cwd=ROOT,
                         capture_output=True, text=True, timeout=120,
                         env={"PATH": "/usr/bin:/bin",
                              "PYTHONPATH": str(ROOT)})
    assert run.returncode == 0, run.stderr
    assert (ROOT / "categorical_bar.png").exists()
    (ROOT / "categorical_bar.png").unlink()
    assert json.loads(spec)["plot_id"] == "categorical.bar"
