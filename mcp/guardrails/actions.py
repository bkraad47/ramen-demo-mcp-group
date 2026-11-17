"""Custom NeMo actions for the demo group's rails. `user_message` is the tool's arguments as JSON (pre);
`bot_message` is the tool's result (post). Deterministic on purpose: the demo costs nothing to run."""

import json

from nemoguardrails.actions import action

INJECTION = ("ignore previous instructions", "ignore all previous instructions", "disregard your instructions")


@action(is_system_action=True)
async def looks_like_injection(context: dict | None = None) -> bool:
    text = ((context or {}).get("user_message") or "").lower()
    return any(p in text for p in INJECTION)


@action(is_system_action=True)
async def mentions_secret(context: dict | None = None) -> bool:
    return "secret" in ((context or {}).get("bot_message") or "").lower()


IRIS_ROW_LIMIT = 50  # CONTRACTS §33.3: the rail's ceiling is fixed; the tool's IRIS_MAX_ROWS may not raise it
IRIS_CELLS = ("sepal_length", "sepal_width", "petal_length", "petal_width", "z")


def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v == v and v not in (float("inf"), float("-inf"))


@action(is_system_action=True)
async def outlier_dump(context: dict | None = None) -> bool:
    """iris_outliers post-rail (1.0.0c): True blocks a result over IRIS_ROW_LIMIT rows, a row whose measurement cells
    are not numbers, or a result that is not the tool's JSON at all (a raw CSV dump). Other tools are never touched."""
    ctx = context or {}
    if ctx.get("tool") != "iris_outliers":
        return False
    try:
        result = json.loads(ctx.get("bot_message") or "")
    except ValueError:
        return True
    rows = result.get("rows") if isinstance(result, dict) else None
    if not isinstance(rows, list) or len(rows) > IRIS_ROW_LIMIT:
        return True
    return any(not isinstance(r, dict) or not all(_is_number(r.get(c)) for c in IRIS_CELLS) for r in rows)
