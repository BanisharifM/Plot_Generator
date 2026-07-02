"""age-encrypted (.age) inputs are decrypted before reading."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import pytest

from core.data_source import DataSource, resolve_local_paths

pytestmark = pytest.mark.skipif(
    not shutil.which("age") or not shutil.which("age-keygen"),
    reason="age not installed")


def test_age_parts_decrypt_and_read_as_one(tmp_path, monkeypatch):
    ident = tmp_path / "id.txt"
    pub = subprocess.run(["age-keygen", "-o", str(ident)],
                         capture_output=True, text=True).stderr
    recip = next(w for w in pub.split() if w.startswith("age1"))

    for i in range(2):
        p = tmp_path / f"part-{i}.parquet"
        pd.DataFrame({"g": ["A", "B"] * 50, "v": range(100)}).to_parquet(p)
        subprocess.run(["age", "-r", recip, "-o", f"{p}.age", str(p)], check=True)
        os.remove(p)

    monkeypatch.setenv("PLAID_AGE_IDENTITY", str(ident))
    hits = resolve_local_paths(str(tmp_path / "part-*.parquet.age"))
    assert len(hits) == 2  # .age accepted by the path validator
    ds = DataSource(hits)
    assert ds.n_rows == 200
    assert ds.tags == {"g": "categorical", "v": "numeric"}
