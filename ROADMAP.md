# Plot Generator — Improvement Roadmap

Produced 2026-07-02 from a full code review (every non-empty file read,
claims verified by execution), measured benchmarks on a generated
2 GB / 33M-row CSV, competitive research of similar tools (PyGWalker,
Tableau, Datawrapper, RawGraphs, Superset, Metabase, SciencePlots),
and big-data plotting best-practice research. Each phase lists its
acceptance tests. Work the phases in order; every phase leaves the app
working.

## The headline numbers (measured on this machine, 2 GB CSV, 33M rows)

| Path | Time | Peak RAM |
|---|---|---|
| Today: `pd.read_csv` whole file (app.py:60) | 32.4 s | 2.8 GB |
| DuckDB aggregate directly on the CSV | 4.4 s | 304 MB |
| DuckDB 2,000-bucket line downsample on CSV | 3.6 s | 1.5 GB |
| CSV -> Parquet conversion, once (ZSTD) | 5.7 s | file: 2 GB -> 583 MB |
| DuckDB aggregate on that Parquet | **0.5 s** | **152 MB** |

Matplotlib render is NOT the bottleneck (1M-point scatter: 0.1 s plot,
4 s savefig at 300 DPI) — but raw millions of points are an unreadable
overplot anyway. Conclusion: **aggregate/downsample in the data layer,
hand matplotlib only what pixels can show (~2K points), keep the
matplotlib/registry rendering architecture.**

---

## Phase 0 — Repair what exists (small, do first)

Broken features and resource bugs, all verified at file:line.

| # | Fix | Where | Verified evidence |
|---|---|---|---|
| 0.1 | Box Plot crash: `labels=` kwarg removed in mpl 3.11 -> use `tick_labels=` (and replace deprecated `vert=`) | plotters/statistical/boxplot.py:86-87 | `TypeError` reproduced in repo venv (mpl 3.11.0) |
| 0.2 | "Seaborn"/"ggplot" presets offered but missing from the presets dict -> silent no-op. Implement via `plt.style.use` or remove from the list | app.py:372 vs 385-416 | presets dict has only IEEE/Nature/Science/Minimal |
| 0.3 | Any non-Default preset re-applies on every rerun and overwrites the Width/Height/DPI/Font sliders -> sliders are dead controls. Apply preset once, on change | app.py:377-378, 420 | execution order in customize_plot_tab |
| 0.4 | Dates never parsed: CSV/Excel/Parquet date columns stay `str`, so the temporal line plot treats dates as categorical strings (label smear, wrong order). Add dtype inference (`parse_dates` / `pd.to_datetime` sniff) at load | utils/data_loader.py:66; line.py:95 rotation branch never fires | measured: `date` col dtype `str` from all formats except JSON |
| 0.5 | Uploaded file re-parsed on EVERY widget interaction (no `st.cache_data`, no guard) | app.py:59-60 | grep: zero `st.cache` in project |
| 0.6 | Figures never closed -> memory leak per plot; plus double-figure leak in bar's grouped recursion | grep `plt.close` = 0 hits; bar.py:67+120-121 | review finding 4-5 |
| 0.7 | Export: sanitize filename (path traversal via `st.text_input`), and add `st.download_button` (today files land server-side in `exports/` only) | core/exporters.py:37; app.py:436 | review finding 8 |
| 0.8 | Sample-load `except Exception` swallows the real error and green-checkmarks fallback data | app.py:83-86 | review finding 9 |
| 0.9 | Scatter UI: X and Y selectboxes both default to column 0 (default plot is x vs x); empty Y multiselect silently discards chosen X (line.py:65-68) | app.py:170-173 | review findings 12, 17 |
| 0.10 | Pin dependencies: `matplotlib>=3.9` + `pyarrow` explicitly (parquet support currently rides a transitive dep), add upper bounds; remove unused deps (seaborn, plotly, networkx, scienceplots*, kaleido, dotenv, pyyaml) — *scienceplots returns in Phase 4 | requirements.txt | pyarrow present only transitively |
| 0.11 | Delete dead code: 24 zero-byte stub files, ~20 never-read settings constants, never-called methods (`prepare_data`, `get_column_info`, `set_regression`, `set_histogram_params`, `set_box_params`, `set_bar_style`) — or wire them up where Phase 3 needs them | inventory in review | grep-verified zero callers |
| 0.12 | Help tab documents 6 plot types that don't exist — sync with registry | app.py:461-507 | |

**Tests (Phase 0):** unit test per plotter that `plot()` succeeds on the
repo's sample CSVs under the pinned matplotlib; a boxplot regression
test; a test that `load_file("typed_dates_missing.csv")` yields
datetime64 for the date column; a rerun-cache test (loader called once);
a figure-count test (`len(plt.get_fignums())` stable across 10 plots);
an export test rejecting `../evil` filenames. Add
`tests/gen_test_data.py` (generator for the typed/unicode/big datasets
used in this audit) so all tests are reproducible at any size.

**Palette verification (measured 2026-07-02, red/green/blue test palette
read back from the rendered artists):** palettes fundamentally WORK in
all 6 registered plotters — line (series colors in order), bar,
scatter, histogram single + grouped, boxplot, heatmap — and every
advertised palette name resolves at any requested size (interpolation
fallback OK). Three caveats: (1) scatter's numeric-color path hardcodes
`cmap='viridis'`, ignoring the palette (scatter.py:85; currently
unreachable from the UI); (2) the heatmap stretches the selected
categorical palette into a continuous colormap — mechanically fine, but
for correlation matrices a DIVERGING palette (already in palettes.py)
is the publication-correct choice; the UI should offer palette KIND by
chart type (fold into Phase 3 shelves); (3) when #series exceeds the
palette length, colors wrap via modulo (4th group reuses color 1) —
acceptable for the 7-color UI palettes, but warn when series > colors.

---

## Phase 1 — Data layer rebuild: DuckDB + Parquet, never load raw data in RAM

Target architecture (validated by the benchmark above):

Engine verdict (researched): **DuckDB** is the single-node standard —
documented out-of-core execution with disk spill and a `memory_limit`
(default 80% RAM); Polars lazy/streaming is the strong second (new
streaming engine not yet default); Vaex is effectively unmaintained;
Dask's own docs call it overkill for single-node few-GB data.

1. **Upload -> spool to disk** (`tempfile` via `getbuffer()`), never
   keep bytes or DataFrames in session state (`st.file_uploader` holds
   the file in per-session RAM, and `st.cache_data` pickles a COPY per
   call — a 2 GB frame multiplies per session). `duckdb.read_csv`
   accepts BytesIO but `read_parquet` does not, so the temp-file spool
   is the robust default. For big local files, also accept a **file
   path** text input (long-open Streamlit feature request #904, the
   standard community pattern) and raise `server.maxUploadSize` via
   `.streamlit/config.toml`.
2. **Sniff, don't read**: schema from DuckDB's sniffer (0.11 s on a
   1.7 GB CSV per their published numbers), preview = `LIMIT 1000`
   plus an honest random sample via `USING SAMPLE reservoir(N ROWS)` —
   shown in a "Check & Describe" step (Datawrapper pattern) where the
   user corrects dtypes (date/categorical/numeric) before plotting.
   This is the "read some lines to get structure, not preview all data"
   principle.
3. **Convert CSV -> Parquet once** (measured here: 5.7 s for 2 GB,
   3.4x smaller; conversion is streaming/bounded-memory); **Parquet
   inputs are used as-is** (native, no conversion). All queries hit
   Parquet with column pruning + row-group zonemap pushdown.
4. **Official DuckDB-in-Streamlit cache pattern**: connection in
   `@st.cache_resource` (shared singleton), small aggregated results in
   `@st.cache_data(ttl=..., max_entries=...)` keyed by the SQL string,
   connection passed as an underscore-prefixed arg.
5. **Hard row ceiling between query and chart** (e.g. 50K), the BI
   precedent: Superset `ROW_LIMIT=50000`, Metabase 2K/10K caps,
   Grafana `maxDataPoints` = panel pixel width. Session state keeps
   only the Parquet path + the chart spec; every chart is one SQL
   query away. Keep a plain-pandas fast path for small files (< ~50 MB)
   if convenient, but DuckDB is the default.

**Tests (Phase 1):** with the 2 GB CSV: preview renders < 2 s; peak
process RSS while plotting < 500 MB (measure via `psutil`); same plot
spec on the small CSV yields identical figure to the pandas path
(golden-image or data-equality test); Parquet upload path works without
conversion; dtype-override roundtrip test.

---

## Phase 2 — Server-side reduction per chart type (the 2M+ samples answer)

Raw rows never meet matplotlib; each registered plotter declares its
**reduction query**:

| Chart | Reduction (SQL in DuckDB) | Points sent to matplotlib |
|---|---|---|
| Bar / grouped / stacked | `GROUP BY category` + agg (mean/sum/count) | ≤ #categories |
| Histogram | binned counts (`width_bucket` / `histogram()`) | #bins |
| Line (temporal) | time-bucketed min/max/mean (M4-style), or LTTB downsample to ~2K buckets | ~2-4K |
| Scatter | if n ≤ 10K: raw points; else 2-D hexbin/density (or stratified sample with a visible "sampled" badge) | ≤ 10K |
| Boxplot / violin | quantiles + whiskers + outlier caps computed in SQL | 5-9 stats/group |
| Heatmap | correlation matrix via SQL/duckdb, or `GROUP BY x,y` counts; annotation only when cells ≤ ~400 (fixes the 10K-row annotate hang, heatmap.py:109-117) | cells |

Downsampling: use **M4** (min/max/first/last per pixel column) as the
line default — provably pixel-error-free rendering at <=4w tuples
(Jugel et al., PVLDB 2014) — with LTTB/MinMaxLTTB optional via the
`tsdownsample` Rust library (what plotly-resampler uses; note
plotly-resampler itself needs Dash callbacks, so in Streamlit we call
the downsampler directly per render). For the scatter high end,
`plt.hexbin` (artist cost bounded by gridsize², not n) or datashader
(documented: a billion points in ~a second on a laptop, with a
matplotlib-native `dsshow` artist). Show an always-visible
"n = 33,000,000 rows, aggregated" caption on reduced plots —
honest-UI rule. Precedent for the whole approach: UW IDL's Mosaic
pushes binning to DuckDB and stays interactive at billions of rows.

**Tests (Phase 2):** golden tests that reduction and full computation
agree on small data (bar means, histogram counts, box quantiles);
line-envelope test (min/max of downsampled == min/max of full);
wall-time budget test on 2 GB (each chart type < 5 s end-to-end);
scatter switches to density at threshold.

---

## Phase 3 — UX rebuild (from the competitive research)

Ranked adoptions (sources: PyGWalker/Graphic Walker, Tableau shelves,
Metabase semantic types, Datawrapper flow, Voyager):

1. **Dtype-tagged encoding shelves**: field list tagged
   categorical/numeric/temporal at load (pandas dtype checks + a
   cardinality heuristic for object columns; works on any unseen
   dataset); X/Y/Color/Size/Facet slots offer ONLY valid columns per
   chart (e.g. heatmap lists numeric columns only — non-numeric never
   shown rather than error-handled). The Check & Describe dtype
   override (Phase 1) is the escape hatch when inference guesses wrong
   (string dates, zip-code "numbers"). Kills the x-vs-x default and
   string-y crashes (validate_data today only counts columns — review
   finding 16). Multi-column slots get an explicit one-click
   "All (valid) columns" affordance in addition to Streamlit's
   built-in dropdown Select-all.
2. **Chart applicability**: each registry entry declares
   `required_encodings` (scatter: 2 numeric; bar: 1 cat + 1 num; line:
   1 temporal/numeric + ≥1 num); picker greys out non-applicable types.
3. **Live re-render, kill the "Create Plot" + no-op "Apply Changes"
   buttons**: Streamlit reruns anyway; with Phase 1 caching, re-render
   on any config change is cheap. (Fixes review finding 11.)
4. **Check & Describe step** between upload and plot (dtype editor,
   Phase 1's sniff UI).
5. **Chart spec as one JSON dict** in session state; save/download/load
   spec (PyGWalker `spec=` pattern) — precondition for code export.
6. Split `app.py` (510 lines) into the existing empty `ui/` modules
   as real components — the stubs finally earn their names.

**Tests (Phase 3):** spec JSON roundtrip; applicability matrix unit
tests (dtype combos -> allowed charts); Streamlit AppTest smoke flows
(upload -> describe -> plot -> customize -> export).

---

## Phase 4 — Publication quality (the app's differentiator)

1. **SciencePlots styles** for IEEE/Nature/Science via
   `plt.style.use(['science','ieee'])`; journal presets become real
   `.mplstyle` compositions instead of the 4-entry dict (templates/*.yaml
   finally used or deleted).
2. **Exact physical sizing**: target-width control = single column
   (3.5 in IEEE) / double (7.16 in) / custom inches / `\textwidth` pt
   helper — figures land in LaTeX at final size, no rescaling (fonts
   keep journal-minimum sizes).
3. **Vector-first export**: PDF/EPS/SVG with fonts embedded, optional
   **PGF** export for exact LaTeX font match; ≥600 DPI raster fallback;
   plus a ready `\begin{figure}...\includegraphics...\end{figure}`
   snippet with the export.
4. **Colorblind support**: Okabe-Ito default (already in palettes.py),
   plus a CVD-simulation preview toggle (Datawrapper pattern) and a
   grayscale-legibility check.

**Tests (Phase 4):** exported PDF has embedded fonts (`pdffonts`);
figure width in the PDF == requested inches (PyMuPDF check); style
presets change rcParams and are reversible; palette contrast checks.

---

## Phase 5 — Code export + new chart types

1. **"Export as Python" for every figure** (requested; PyGWalker
   `to_code()` / Mito precedent): a standalone runnable script that
   (a) references the data FILE PATH (never inlines rows — data can be
   2M+ samples), (b) contains the exact reduction step (the DuckDB SQL
   or pandas equivalent from Phase 2), (c) matplotlib code with the
   full PlotConfig styling, (d) `savefig` at the configured size/DPI.
   Running the script reproduces the figure at any data size.
2. Implement the stub chart types through the same registry + reduction
   contract: violin, area, stacked/grouped bar as first-class, pie
   (with a "consider a bar" nudge), then faceting/small multiples
   (seaborn.objects or manual subplot grid).
3. Optional additive tab: PyGWalker "free explore" for data
   investigation before figure-building (research verdict: wrap it as a
   side tab, do NOT build the core on it — it can't do matplotlib/PDF/
   journal output).

**Tests (Phase 5):** for each chart: export code -> run script in a
clean venv -> byte/pixel-compare the produced file with the app's
export (allowing font rasterization tolerance); code runs against the
2 GB file within the same time budget.

---

## Phase 6 — Hardening & CI

- pytest suite from all phases wired into GitHub Actions (the repo has
  zero tests today); ruff + formatting; pinned lockfile.
- Error surfacing policy: no bare `except Exception` without showing
  the message; no success-banners on fallbacks.
- README with screenshots, quickstart, and the architecture sketch
  (currently one line).

---

## Test datasets (already generated during this audit)

Regenerate any size with `tests/gen_test_data.py` (to be added, Phase 0):

| Dataset | Purpose |
|---|---|
| `typed_dates_missing.csv` (500 rows: dates, categorical with None, ints, floats with NaN) | dtype inference, missing-value handling |
| `typed.xlsx` / `typed.json` / `typed.parquet` | loader parity across formats (incl. Parquet input requirement) |
| `unicode_headers.csv` ("München (°C)", "growth %") | header robustness |
| `big.csv` — 2.0 GB, 33M rows, 8 cols (ts, 2 categoricals, 5 numerics) | scale benchmarks, Phase 1/2 acceptance |
| `big.csv.parquet` — 583 MB ZSTD | Parquet-native path |

## Suggested order & sizing

Phase 0: S (a day-ish of focused work) -> immediate correctness.
Phase 1: M — the single highest-value change (60x speed, 18x memory).
Phase 2: M — makes every chart honest at scale.
Phase 3: M — the UX becomes competitive.
Phase 4: M — the academic differentiator.
Phase 5: S-M — reproducibility story.
Phase 6: S — keeps it all true.

## Key sources (verified by the research pass)

- DuckDB in Streamlit (official cache pattern): duckdb.org/2025/03/28/using-duckdb-in-streamlit
- DuckDB out-of-core & memory_limit: duckdb.org/docs/current/guides/performance/how_to_tune_workloads.html
- Parquet pushdown & row-group guidance: duckdb.org/docs/current/data/parquet/overview.html, /guides/performance/file_formats.html
- CSV vs Parquet (TPC-H: ~5x size, ~7x query): duckdb.org/2024/12/05/csv-files-dethroning-parquet-or-not
- Sampling for previews: duckdb.org/docs/current/sql/samples.html
- Streamlit caching semantics (cache_data copies, cache_resource singleton): docs.streamlit.io/develop/concepts/architecture/caching
- M4 pixel-exact downsampling: Jugel et al., PVLDB 7(10) 2014 — vldb.org/pvldb/vol7/p797-jugel.pdf
- LTTB: Steinarsson 2013 — skemman.is/handle/1946/15343; MinMaxLTTB: arXiv:2305.00332; tsdownsample: github.com/predict-idlab/tsdownsample
- Datashader pipeline & dsshow: datashader.org/getting_started/Introduction.html
- BI row limits: Superset config.py ROW_LIMIT; Metabase query-builder caps; Grafana maxDataPoints docs
- Mosaic (DuckDB-backed, billions of rows): idl.uw.edu/mosaic (TVCG 2024)
- SciencePlots: github.com/garrettj403/SciencePlots; PGF backend: matplotlib.org/stable/users/explain/text/pgf.html
- Figure sizing for LaTeX: jwalton.info/Embed-Publication-Matplotlib-Latex; IEEE sizes: journals.ieeeauthorcenter.ieee.org
- PyGWalker (spec/save/to_code precedent): github.com/Kanaries/pygwalker; Tableau shelves; Datawrapper colorblind check: datawrapper.de/blog/colorblind-check
- Engine landscape: docs.pola.rs/user-guide/concepts/streaming (Polars streaming, non-default); docs.dask.org best practices (single-node guidance); vaex maintenance status: github.com/vaexio/vaex/discussions/2363
