"""Per-group means of the Iris columns with pandas; rendered by the iris_chart app (CONTRACTS §33.1, §33.3)."""
from pathlib import Path

import pandas as pd

CSV = Path(__file__).resolve().parents[2] / "resources" / "iris_csv" / "iris.csv"
NUMERIC = ["sepal_length", "sepal_width", "petal_length", "petal_width"]


def group_means(by: str = "species") -> dict:
    df = pd.read_csv(CSV)
    if by not in df.columns or by in NUMERIC:
        raise ValueError(f"by must name a categorical column of the Iris data: species (got {by!r})")
    g = df.groupby(by, sort=True)
    means = g[NUMERIC].mean().round(3)
    return {
        "by": by,
        "counts": {str(k): int(v) for k, v in g.size().items()},
        "groups": {str(k): {c: float(means.loc[k, c]) for c in NUMERIC} for k in means.index},
    }
