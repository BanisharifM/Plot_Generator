"""Reductions must agree with full-data pandas computations."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import pytest

from core.data_source import ROW_LIMIT, DataSource
from core.reductions import LINE_BUCKETS, reduce_for_plot


@pytest.fixture
def source(tmp_path):
    n = ROW_LIMIT + 10_000
    rng = np.random.default_rng(1)
    df = pd.DataFrame({
        "cat": rng.choice(list("ABC"), n),
        "t": np.arange(n, dtype=float),
        "v": rng.normal(10, 2, n),
    })
    p = tmp_path / "d.parquet"
    df.to_parquet(p)
    return DataSource(str(p)), df


def test_bar_groupby_matches_pandas_over_all_rows(source):
    ds, df = source
    out, caption = reduce_for_plot(ds, "categorical.bar",
                                   {"x_column": "cat", "y_columns": ["v"]})
    expected = df.groupby("cat")["v"].mean().sort_index()
    got = out.set_index("cat")["v"].sort_index()
    assert np.allclose(got.values, expected.values)
    assert "all" in caption


def test_line_bucketed_to_target_and_ordered(source):
    ds, df = source
    out, caption = reduce_for_plot(ds, "temporal.line",
                                   {"x_column": "t", "y_columns": ["v"]})
    assert len(out) == LINE_BUCKETS
    assert out["t"].is_monotonic_increasing
    assert abs(out["v"].mean() - df["v"].mean()) < 0.05
    assert "bucket" in caption


def test_distribution_charts_get_unbiased_sample(source):
    ds, df = source
    out, caption = reduce_for_plot(ds, "statistical.histogram",
                                   {"value_column": "v"})
    assert len(out) == ROW_LIMIT and list(out.columns) == ["v"]
    assert abs(out["v"].mean() - df["v"].mean()) < 0.05
    assert "sample" in caption


def test_small_data_passes_through_unreduced(tmp_path):
    p = tmp_path / "s.parquet"
    pd.DataFrame({"x": [1, 2], "y": [3.0, 4.0]}).to_parquet(p)
    out, caption = reduce_for_plot(DataSource(str(p)), "statistical.scatter",
                                   {"x_column": "x", "y_column": "y"})
    assert len(out) == 2 and caption is None
