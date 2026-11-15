"""Unit tests for the Iris example (CONTRACTS §33.3): `python -m pytest` in the repo root, pandas + pytest installed."""
import asyncio
import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

MCP = Path(__file__).resolve().parents[1] / "mcp"


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


describe = _load(MCP / "tools/iris_describe/iris_describe.py").describe
outliers = _load(MCP / "tools/iris_outliers/iris_outliers.py").outliers
group_means = _load(MCP / "tools/iris_group_means/iris_group_means.py").group_means
read_csv = _load(MCP / "resources/iris_csv/iris_csv.py").read_csv


@pytest.fixture
def actions():
    """mcp/guardrails/actions.py without nemoguardrails installed: stub the decorator."""
    fake = types.ModuleType("nemoguardrails.actions")
    fake.action = lambda **_: (lambda f: f)
    sys.modules.setdefault("nemoguardrails", types.ModuleType("nemoguardrails"))
    sys.modules["nemoguardrails.actions"] = fake
    return _load(MCP / "guardrails/actions.py")


def test_csv_has_150_rows_and_the_exact_header():
    lines = read_csv().splitlines()
    assert lines[0] == "sepal_length,sepal_width,petal_length,petal_width,species"
    assert len(lines) == 151


def test_describe_counts_150_and_matches_the_known_means():
    d = describe()
    assert d["count"] == 150
    assert set(d["columns"]) == {"sepal_length", "sepal_width", "petal_length", "petal_width"}
    assert d["columns"]["sepal_length"]["count"] == 150
    assert d["columns"]["sepal_length"]["mean"] == 5.8433
    assert d["columns"]["sepal_width"]["std"] == 0.4359
    assert (d["columns"]["petal_length"]["min"], d["columns"]["petal_length"]["max"]) == (1.0, 6.9)


def test_outliers_sepal_width_z_2_5_is_two_rows():
    r = outliers("sepal_width", 2.5)
    assert r["total"] == 2 and len(r["rows"]) == 2 and r["truncated"] is False and r["limit"] == 50
    assert sorted(row["sepal_width"] for row in r["rows"]) == [4.2, 4.4]
    assert all(row["species"] == "setosa" and row["z"] > 2.5 for row in r["rows"])


def test_outliers_default_z_and_bad_arguments():
    assert outliers("petal_length")["z"] == 2.5
    with pytest.raises(ValueError):
        outliers("species", 2.5)
    with pytest.raises(ValueError):
        outliers("sepal_width", 0)


def test_outliers_cap_at_50_rows_and_honour_iris_max_rows(monkeypatch):
    monkeypatch.delenv("IRIS_MAX_ROWS", raising=False)
    r = outliers("sepal_width", 0.001)
    assert r["total"] == 150 and len(r["rows"]) == 50 and r["truncated"] is True
    monkeypatch.setenv("IRIS_MAX_ROWS", "10")
    r = outliers("sepal_width", 0.001)
    assert r["limit"] == 10 and len(r["rows"]) == 10 and r["truncated"] is True
    monkeypatch.setenv("IRIS_MAX_ROWS", "nope")
    assert outliers("sepal_width", 2.5)["limit"] == 50


def test_group_means_has_three_species_with_the_known_means():
    g = group_means("species")
    assert g["by"] == "species" and g["counts"] == {"setosa": 50, "versicolor": 50, "virginica": 50}
    assert g["groups"]["setosa"] == {"sepal_length": 5.006, "sepal_width": 3.428, "petal_length": 1.462, "petal_width": 0.246}
    assert g["groups"]["virginica"]["petal_length"] == 5.552
    with pytest.raises(ValueError):
        group_means("sepal_length")


def _rail(actions, tool, result):
    ctx = {"tool": tool, "bot_message": result if isinstance(result, str) else json.dumps(result)}
    return asyncio.run(actions.outlier_dump(ctx))


def test_outlier_rail_passes_a_normal_result(actions):
    assert _rail(actions, "iris_outliers", outliers("sepal_width", 2.5)) is False


def test_outlier_rail_blocks_more_than_50_rows(actions, monkeypatch):
    monkeypatch.setenv("IRIS_MAX_ROWS", "150")
    r = outliers("sepal_width", 0.001)
    assert len(r["rows"]) == 150
    assert _rail(actions, "iris_outliers", r) is True


def test_outlier_rail_blocks_non_numeric_cells_and_text_dumps(actions):
    r = outliers("sepal_width", 2.5)
    r["rows"][0]["sepal_width"] = "4.4; DROP TABLE"
    assert _rail(actions, "iris_outliers", r) is True
    assert _rail(actions, "iris_outliers", read_csv()) is True
    assert _rail(actions, "word_count", read_csv()) is False
