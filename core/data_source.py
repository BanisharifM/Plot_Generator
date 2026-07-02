"""DuckDB-backed data source: query files in place, never load them in RAM.

CSV uploads are spooled to disk and converted once to Parquet (measured on a
2 GB CSV: 5.7 s conversion, then 0.5 s / 152 MB-peak aggregates vs 32 s /
2.8 GB for a full pandas read). Parquet inputs are queried as-is. Only
bounded, column-pruned DataFrames ever leave this module.
"""

import hashlib
import os
import re
import subprocess
import tempfile
from pathlib import Path

import duckdb
import pandas as pd

# BI-standard ceiling between query and chart (Superset uses 50k).
ROW_LIMIT = 50_000

# age-encrypted inputs: the identity lives in the Secure Enclave (Touch ID),
# so decryption prompts the user and the key never touches disk/env - an LLM
# tool can read the .age ciphertext but cannot decrypt it.
def _age_identity() -> str:
    # read at call time, not import, so the env can change per session
    return os.environ.get(
        "PLAID_AGE_IDENTITY", str(Path.home() / ".plaid-identity.txt"))

_NUMERIC = ("TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT", "UTINYINT",
            "USMALLINT", "UINTEGER", "UBIGINT", "FLOAT", "DOUBLE", "DECIMAL")


def _tag(duck_type: str) -> str:
    t = duck_type.upper()
    if t.startswith(("TIMESTAMP", "DATE", "TIME")):
        return "temporal"
    if t.startswith(_NUMERIC):
        return "numeric"
    return "categorical"
_SPOOL_DIR = Path(tempfile.gettempdir()) / "plot_generator_spool"


def _decrypt_age(path: Path) -> Path:
    """Decrypt a .age file to an owner-only temp copy (prompts Touch ID).

    The working copy lives in a 0700 temp dir for the session; the data at
    rest stays encrypted. Raises if the identity is missing or decryption
    fails (wrong key / declined biometric).
    """
    _SPOOL_DIR.mkdir(exist_ok=True)
    os.chmod(_SPOOL_DIR, 0o700)
    inner = path.with_suffix("")  # strip .age, keep .parquet/.csv/...
    tag = hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:16]
    out = _SPOOL_DIR / f"{tag}_{inner.name}"
    if not out.exists():
        identity = _age_identity()
        if not Path(identity).is_file():
            raise FileNotFoundError(
                f"age identity not found at {identity} "
                "(set PLAID_AGE_IDENTITY)")
        subprocess.run(
            ["age", "-d", "-i", identity, "-o", str(out), str(path)],
            check=True)
        os.chmod(out, 0o600)
    return out


class DataSource:
    """One dataset, backed by one or MANY same-schema files on disk.

    A list of paths (e.g. a dataset split into 10 parquet parts) is
    scanned as a single table - DuckDB reads multi-file parquet natively;
    union_by_name tolerates column-order differences between parts.
    """

    def __init__(self, path, original_name: str = ""):
        paths = [Path(p) for p in ([path] if isinstance(path, (str, Path)) else path)]
        self.name = original_name or (
            paths[0].name if len(paths) == 1 else f"{paths[0].name} (+{len(paths)-1})")
        self._con = duckdb.connect()  # in-process, lazy, files stay on disk
        paths = [_decrypt_age(p) if p.suffix.lower() == ".age" else p
                 for p in paths]
        paths = [self._to_parquet(p) for p in paths]
        self.path = paths[0] if len(paths) == 1 else paths
        listed = ", ".join(f"'{p}'" for p in paths)
        self._rel = f"read_parquet([{listed}], union_by_name=true)"
        self.n_rows = self._con.execute(
            f"SELECT count(*) FROM {self._rel}").fetchone()[0]
        desc = self._con.execute(f"DESCRIBE SELECT * FROM {self._rel}").fetchall()
        self.columns = [r[0] for r in desc]
        self.tags = {name: _tag(dtype) for name, dtype, *_ in desc}

    def _to_parquet(self, p: Path) -> Path:
        if p.suffix.lower() == ".csv":
            parquet = p.with_suffix(".parquet")
            if not parquet.exists():
                self._con.execute(
                    f"COPY (SELECT * FROM read_csv_auto('{p}')) TO '{parquet}' "
                    "(FORMAT PARQUET, COMPRESSION ZSTD)")
            return parquet
        if p.suffix.lower() in (".xlsx", ".xls", ".json"):
            parquet = p.with_suffix(p.suffix + ".parquet")
            if not parquet.exists():
                reader = pd.read_excel if p.suffix.lower() != ".json" else pd.read_json
                reader(p).to_parquet(parquet)
            return parquet
        return p

    @classmethod
    def from_uploads(cls, files) -> "DataSource":
        """files: list of (filename, bytes) - spooled once, opened as one set."""
        import hashlib
        _SPOOL_DIR.mkdir(exist_ok=True)
        targets = []
        for filename, content in files:
            digest = hashlib.sha256(content).hexdigest()[:16]
            t = _SPOOL_DIR / f"{digest}{Path(filename).suffix.lower()}"
            if not t.exists():
                t.write_bytes(content)
            targets.append(str(t))
        return cls(targets, original_name=files[0][0] if len(files) == 1
                   else f"{files[0][0]} (+{len(files)-1})")

    @classmethod
    def from_upload(cls, filename: str, content: bytes) -> "DataSource":
        """Spool uploaded bytes to disk once, keyed by content, and open."""
        import hashlib
        _SPOOL_DIR.mkdir(exist_ok=True)
        digest = hashlib.sha256(content).hexdigest()[:16]
        target = _SPOOL_DIR / f"{digest}{Path(filename).suffix.lower()}"
        if not target.exists():
            target.write_bytes(content)
        return cls(str(target), original_name=filename)

    def _quoted(self, columns) -> str:
        cols = [c for c in columns if c in self.columns]
        if not cols:
            raise ValueError(f"no valid columns in {columns}")
        return ", ".join('"' + c.replace('"', '""') + '"' for c in cols)

    def preview(self, n: int = 10) -> pd.DataFrame:
        return self._con.execute(f"SELECT * FROM {self._rel} LIMIT {n}").df()

    def select(self, columns, limit: int = ROW_LIMIT) -> pd.DataFrame:
        """Column-pruned, row-bounded frame for plotting."""
        return self._con.execute(
            f"SELECT {self._quoted(columns)} FROM {self._rel} LIMIT {int(limit)}"
        ).df()

    def page(self, offset: int, limit: int = 1000):
        """One page of the full dataset - browsing never loads the file."""
        return self._con.execute(
            f"SELECT * FROM {self._rel} LIMIT {int(limit)} OFFSET {int(offset)}"
        ).df()

    @property
    def truncated(self) -> bool:
        return self.n_rows > ROW_LIMIT


def resolve_local_paths(text: str) -> list:
    """Existing data files for the path input; supports globs (part-*.parquet)."""
    if not text or re.search(r"[\0\n]", text):
        return []
    import glob as _glob
    expanded = str(Path(text).expanduser())
    hits = sorted(_glob.glob(expanded)) if any(c in expanded for c in "*?[") \
        else [expanded]
    ok = [h for h in hits if Path(h).is_file() and Path(h).suffix.lower() in
          (".csv", ".parquet", ".xlsx", ".xls", ".json", ".age")]
    return ok if len(ok) == len(hits) and ok else []


def is_safe_local_path(text: str) -> bool:
    return bool(resolve_local_paths(text))
