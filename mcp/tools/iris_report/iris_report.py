"""A short prose report on the Iris data for a free-text question, computed with pandas (Ramen 1.0.0c, CONTRACTS §36.4).
The LLM rails around this tool live in mcp/guardrails.yaml; the tool itself never calls a model."""
import re
from pathlib import Path

import pandas as pd

CSV = Path(__file__).resolve().parents[2] / "resources" / "iris_csv" / "iris.csv"
NUMERIC = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
SPECIES = ["setosa", "versicolor", "virginica"]
MAX_QUESTION = 500


def columns_in(question: str) -> list[str]:
    q = question.lower().replace("-", " ").replace("_", " ")
    found = [c for c in NUMERIC if c.replace("_", " ") in q]
    return found or NUMERIC


def wants_species(question: str) -> bool:
    q = question.lower()
    return bool(re.search(r"species|group|per |by |across", q)) or any(s in q for s in SPECIES)


def report(question: str) -> str:
    question = question.strip()
    if not question:
        raise ValueError("question must not be empty")
    if len(question) > MAX_QUESTION:
        raise ValueError(f"question must be at most {MAX_QUESTION} characters")
    df = pd.read_csv(CSV)
    cols = columns_in(question)
    lines = [f"The Iris data set has {len(df)} rows in {len(SPECIES)} species."]
    for c in cols:
        s = df[c]
        lines.append(
            f"{c.replace('_', ' ').capitalize()}: mean {s.mean():.2f} cm, std {s.std():.2f}, "
            f"range {s.min():.1f} to {s.max():.1f} cm."
        )
    if wants_species(question):
        means = df.groupby("species")[cols].mean()
        for c in cols:
            parts = ", ".join(f"{sp} {means.loc[sp, c]:.2f}" for sp in SPECIES)
            lines.append(f"Mean {c.replace('_', ' ')} per species: {parts}.")
    return " ".join(lines)
