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


# ---- iris_report (1.0.0c, CONTRACTS §36.4): pandas prose, no model inside the tool ------------------------------------
report = _load(MCP / "tools/iris_report/iris_report.py").report


def test_report_names_the_columns_the_question_asks_about():
    r = report("How does sepal width vary across the three species?")
    text = r["report"]
    assert text.startswith("The Iris data set has 150 rows across setosa, versicolor and virginica.")
    assert "Sepal width: mean 3.06 cm, std 0.44, range 2.0 to 4.4 cm." in text
    assert "Mean sepal width per species: setosa 3.43, versicolor 2.77, virginica 2.97." in text
    assert "petal" not in text.lower()
    # the numbers the prose cites travel with it, so the hallucination rail checks the text against the tool's data
    assert r["rows"] == 150 and r["species"] == ["setosa", "versicolor", "virginica"]
    assert r["columns"] == {"sepal_width": {"mean": 3.06, "std": 0.44, "min": 2.0, "max": 4.4}}
    assert r["group_means"] == {"sepal_width": {"setosa": 3.43, "versicolor": 2.77, "virginica": 2.97}}


def test_every_number_in_the_prose_is_in_the_structured_data():
    import re

    for q in ("How does sepal width vary across the three species?", "Give me a summary", "petal length by species"):
        r = report(q)
        data = json.dumps({k: v for k, v in r.items() if k != "report"})
        cited = set(re.findall(r"\d+(?:\.\d+)?", r["report"]))
        assert cited <= set(re.findall(r"\d+(?:\.\d+)?", data)), (q, cited)


def test_report_covers_every_column_without_species_when_the_question_names_none():
    r = report("Give me a summary")
    assert set(r["columns"]) == {"sepal_length", "sepal_width", "petal_length", "petal_width"}
    assert "per species" not in r["report"] and "Petal length: mean 3.76 cm" in r["report"] and r["group_means"] == {}


def test_report_rejects_empty_and_oversized_questions():
    with pytest.raises(ValueError):
        report("   ")
    with pytest.raises(ValueError):
        report("x" * 501)


def test_guardrails_yaml_names_the_1_0_0c_rails():
    """The shapes the worker parses (§36.1): a list of names, a {name: options} item, rails at the right stage."""
    import yaml

    doc = yaml.safe_load((MCP / "guardrails.yaml").read_text())
    assert doc["tools"]["iris_outliers"] == {"post": ["self_check_output"]}
    rep = doc["tools"]["iris_report"]
    assert rep["pre"][:2] == ["self_check_input", "jailbreak_detection"]
    assert rep["pre"][2] == {"topical": {"topics": ["iris", "statistics"]}}
    assert rep["post"] == ["hallucination"]
    cfg = yaml.safe_load((MCP / "guardrails/config.yml").read_text())
    assert cfg["models"] == [], "the worker fills models: from the group's provider; no key lives in the repo"
    prompts = {p["task"] for p in yaml.safe_load((MCP / "guardrails/prompts.yml").read_text())["prompts"]}
    assert prompts == {"self_check_input", "self_check_output"}
