"""Rows of the Iris data whose |z-score| on one column exceeds z; at most IRIS_MAX_ROWS rows (CONTRACTS §33.3)."""
import os
from pathlib import Path

import pandas as pd

CSV = Path(__file__).resolve().parents[2] / "resources" / "iris_csv" / "iris.csv"
NUMERIC = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
DEFAULT_LIMIT = 50


def row_limit() -> int:
    raw = os.environ.get("IRIS_MAX_ROWS", "").strip()
    return int(raw) if raw.isdigit() and int(raw) > 0 else DEFAULT_LIMIT


def outliers(column: str, z: float = 2.5) -> dict:
    if column not in NUMERIC:
        raise ValueError(f"column must be one of {NUMERIC}, got {column!r}")
    if not z > 0:
        raise ValueError("z must be a positive number such as 2.5")
    df = pd.read_csv(CSV)
    col = df[column]
    df["z"] = ((col - col.mean()) / col.std()).round(3)
    hits = df[df["z"].abs() > z]
    limit = row_limit()
    rows = [
        {"index": int(i), **{c: float(r[c]) for c in NUMERIC}, "species": str(r["species"]), "z": float(r["z"])}
        for i, r in hits.head(limit).iterrows()
    ]
    return {"column": column, "z": float(z), "total": int(len(hits)), "limit": limit, "truncated": len(hits) > limit, "rows": rows}
