"""Dtype gating: invalid columns never offered; charts hide when unusable."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from core.data_source import DataSource
from core.encodings import applicable, valid_columns


def _source(tmp_path, df):
    p = tmp_path / "d.parquet"
    df.to_parquet(p)
    return DataSource(str(p))


def test_tags_from_duckdb_types(tmp_path):
    ds = _source(tmp_path, pd.DataFrame({
        "when": pd.date_range("2024-01-01", periods=3),
        "who": ["a", "b", "c"],
        "how_much": [1.0, 2.0, 3.0],
    }))
    assert ds.tags == {"when": "temporal", "who": "categorical",
                      "how_much": "numeric"}


def test_heatmap_offers_only_numeric(tmp_path):
    ds = _source(tmp_path, pd.DataFrame({
        "city": ["x", "y"], "t": [1.0, 2.0], "p": [3.0, 4.0]}))
    assert valid_columns(ds, "statistical.heatmap", "value_columns") == ["t", "p"]
    assert applicable(ds, "statistical.heatmap")


def test_charts_hidden_when_no_valid_columns(tmp_path):
    ds = _source(tmp_path, pd.DataFrame({"name": ["a", "b"]}))  # text only
    assert not applicable(ds, "statistical.scatter")
    assert not applicable(ds, "temporal.line")
