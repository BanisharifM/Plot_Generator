"""Per-chart server-side reduction: charts reflect ALL rows, not the first N.

Bar charts aggregate with GROUP BY, lines are bucket-averaged to ~2000
points, and distribution charts (histogram/box/scatter/heatmap) get an
unbiased reservoir sample instead of a biased first-N slice. Everything
runs in DuckDB over the Parquet file; matplotlib only sees the result.
"""


from core.data_source import ROW_LIMIT, DataSource

LINE_BUCKETS = 2_000
MAX_CATEGORIES = 500


def _q(col: str) -> str:
    return '"' + col.replace('"', '""') + '"'


def reduce_for_plot(source: DataSource, plot_id: str, params: dict):
    """Return (dataframe, caption) sized for the chart type."""
    n = source.n_rows
    con, rel = source._con, source._rel

    if plot_id == "categorical.bar" and params.get("x_column"):
        x = _q(params["x_column"])
        ys = ", ".join(f"avg({_q(y)}) AS {_q(y)}" for y in params.get("y_columns", []))
        if ys:
            df = con.execute(
                f"SELECT {x}, {ys} FROM {rel} GROUP BY {x} ORDER BY {x} "
                f"LIMIT {MAX_CATEGORIES}").df()
            return df, f"mean per category over all {n:,} rows"

    if plot_id == "temporal.line" and params.get("x_column") and n > ROW_LIMIT:
        x = _q(params["x_column"])
        ys = ", ".join(f"avg({_q(y)}) AS {_q(y)}" for y in params.get("y_columns", []))
        if ys:
            df = con.execute(
                f"SELECT min({x}) AS {x}, {ys} FROM ("
                f"  SELECT *, ntile({LINE_BUCKETS}) OVER (ORDER BY {x}) AS __b"
                f"  FROM {rel}) GROUP BY __b ORDER BY 1").df()
            return df, f"{LINE_BUCKETS:,}-bucket mean of all {n:,} rows"

    # distribution charts: unbiased reservoir sample beats a first-N slice
    cols = []
    for v in params.values():
        cols += v if isinstance(v, list) else [v] if isinstance(v, str) else []
    cols = [c for c in dict.fromkeys(cols) if c in source.columns] or source.columns
    quoted = ", ".join(_q(c) for c in cols)
    if n > ROW_LIMIT:
        df = con.execute(
            f"SELECT {quoted} FROM {rel} "
            f"USING SAMPLE reservoir({ROW_LIMIT} ROWS) REPEATABLE (42)").df()
        return df, f"random sample of {ROW_LIMIT:,} of {n:,} rows"
    return con.execute(f"SELECT {quoted} FROM {rel}").df(), None
