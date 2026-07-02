"""DataSource: in-place querying, Parquet conversion, bounded output."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import pytest

from core.data_source import ROW_LIMIT, DataSource, is_safe_local_path


@pytest.fixture
def csv_path(tmp_path):
    n = ROW_LIMIT + 5_000  # bigger than the ceiling
    rng = np.random.default_rng(0)
    p = tmp_path / "data.csv"
    pd.DataFrame({
        "sensor": rng.choice(list("AB"), n),
        "temperature": rng.normal(20, 5, n),
        "pressure": rng.normal(1013, 8, n),
    }).to_csv(p, index=False)
    return p


def test_csv_converted_once_and_counted(csv_path):
    ds = DataSource(str(csv_path))
    assert ds.path.suffix == ".parquet" and ds.path.exists()
    assert ds.n_rows == ROW_LIMIT + 5_000
    assert ds.columns == ["sensor", "temperature", "pressure"]
    assert ds.truncated


def test_select_prunes_columns_and_bounds_rows(csv_path):
    ds = DataSource(str(csv_path))
    df = ds.select(["temperature"])
    assert list(df.columns) == ["temperature"]
    assert len(df) == ROW_LIMIT
    assert len(ds.preview(7)) == 7


def test_parquet_used_as_is(tmp_path):
    p = tmp_path / "d.parquet"
    pd.DataFrame({"a": [1, 2, 3]}).to_parquet(p)
    ds = DataSource(str(p))
    assert ds.path == p and ds.n_rows == 3 and not ds.truncated


def test_upload_spool_dedupes(tmp_path):
    content = b"a,b\n1,2\n3,4\n"
    d1 = DataSource.from_upload("x.csv", content)
    d2 = DataSource.from_upload("x.csv", content)
    assert d1.path == d2.path
    assert d1.n_rows == 2


def test_select_rejects_unknown_columns(csv_path):
    ds = DataSource(str(csv_path))
    with pytest.raises(ValueError):
        ds.select(["nope"])


def test_is_safe_local_path(csv_path, tmp_path):
    assert is_safe_local_path(str(csv_path))
    assert not is_safe_local_path(str(tmp_path))          # a directory
    assert not is_safe_local_path("/does/not/exist.csv")
    assert not is_safe_local_path("data.txt\nrm -rf /")
