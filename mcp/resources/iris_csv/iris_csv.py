"""Iris resource: the CSV next to this file, served as text/csv."""
from pathlib import Path


def read_csv() -> str:
    return (Path(__file__).resolve().parent / "iris.csv").read_text(encoding="utf-8")
