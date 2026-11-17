"""A short prose report on the Iris data for a free-text question, computed with pandas (Ramen 1.0.0c, CONTRACTS §36.4).
The result carries the numbers the prose cites (`columns`, `group_means`) so the hallucination rail checks the text
against the tool's own data. The tool itself never calls a model; its rails live in mcp/guardrails.yaml."""
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


def report(question: str) -> dict:
    question = question.strip()
    if not question:
        raise ValueError("question must not be empty")
    if len(question) > MAX_QUESTION:
        raise ValueError(f"question must be at most {MAX_QUESTION} characters")
    df = pd.read_csv(CSV)
    cols = columns_in(question)
    columns = {
        c: {"mean": round(float(df[c].mean()), 2), "std": round(float(df[c].std()), 2),
            "min": round(float(df[c].min()), 1), "max": round(float(df[c].max()), 1)}
        for c in cols
    }
    lines = [f"The Iris data set has {len(df)} rows across {SPECIES[0]}, {SPECIES[1]} and {SPECIES[2]}."]
    for c, s in columns.items():
        lines.append(
            f"{c.replace('_', ' ').capitalize()}: mean {s['mean']} cm, std {s['std']}, "
            f"range {s['min']} to {s['max']} cm."  # the rounded values' own repr: prose and data match exactly
        )
    group_means: dict = {}
    if wants_species(question):
        means = df.groupby("species")[cols].mean()
        for c in cols:
            group_means[c] = {sp: round(float(means.loc[sp, c]), 2) for sp in SPECIES}
            parts = ", ".join(f"{sp} {group_means[c][sp]}" for sp in SPECIES)
            lines.append(f"Mean {c.replace('_', ' ')} per species: {parts}.")
    return {
        "report": " ".join(lines),
        "rows": int(len(df)),
        "species": SPECIES,
        "columns": columns,
        "group_means": group_means,
    }
