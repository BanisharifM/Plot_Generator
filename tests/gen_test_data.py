"""Generate the audit's test datasets at any size (see ROADMAP.md).

Usage: python tests/gen_test_data.py OUT_DIR [n_million_rows]
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd


def typed(out: Path, n=500, seed=7):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "date": pd.date_range("2023-01-01", periods=n, freq="D").strftime("%Y-%m-%d"),
        "category": rng.choice(["alpha", "beta", "gamma", None], n, p=[.4, .3, .2, .1]),
        "count": rng.poisson(30, n),
        "revenue": rng.lognormal(3, .5, n).round(2),
    })
    df.loc[rng.choice(n, n // 20, replace=False), "revenue"] = np.nan
    df.to_csv(out / "typed_dates_missing.csv", index=False)
    df.to_excel(out / "typed.xlsx", index=False)
    df.to_json(out / "typed.json", orient="records")
    df.to_parquet(out / "typed.parquet")
    pd.DataFrame({"München (°C)": rng.normal(9, 3, 50).round(1),
                  "growth %": rng.normal(2, 1, 50).round(2)}
                 ).to_csv(out / "unicode_headers.csv", index=False)


def big(out: Path, millions=1, seed=0):
    rng = np.random.default_rng(seed)
    path = out / "big.csv"
    rows = 1_000_000
    for i in range(millions):
        pd.DataFrame({
            "ts": pd.date_range("2024-01-01", periods=rows, freq="s") + pd.Timedelta(days=12 * i),
            "sensor": rng.choice(list("ABCDEFGH"), rows),
            "region": rng.choice(["north", "south", "east", "west"], rows),
            "temperature": rng.normal(20, 5, rows).round(3),
            "pressure": rng.normal(1013, 8, rows).round(3),
            "value": rng.normal(0, 1, rows).round(5),
        }).to_csv(path, mode="w" if i == 0 else "a", header=(i == 0), index=False)
        print(f"chunk {i + 1}/{millions}", flush=True)


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("test_data")
    out.mkdir(exist_ok=True)
    typed(out)
    if len(sys.argv) > 2:
        big(out, int(sys.argv[2]))
    print(f"written to {out}/")
