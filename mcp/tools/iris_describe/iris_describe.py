"""Per-column count/mean/std/min/max of the Iris data with pandas (CONTRACTS §33.3)."""
from pathlib import Path

import pandas as pd

CSV = Path(__file__).resolve().parents[2] / "resources" / "iris_csv" / "iris.csv"
NUMERIC = ["sepal_length", "sepal_width", "petal_length", "petal_width"]


def describe() -> dict:
    df = pd.read_csv(CSV)
    stats = df[NUMERIC].describe().loc[["count", "mean", "std", "min", "max"]].round(4)
    columns = {c: {k: (int(v) if k == "count" else float(v)) for k, v in stats[c].items()} for c in NUMERIC}
    return {"count": int(len(df)), "columns": columns}
