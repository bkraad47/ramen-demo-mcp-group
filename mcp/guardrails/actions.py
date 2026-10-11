"""Custom NeMo actions for the demo group's rails. `user_message` is the tool's arguments as JSON (pre);
`bot_message` is the tool's result (post). Deterministic on purpose: the demo costs nothing to run."""

from nemoguardrails.actions import action

INJECTION = ("ignore previous instructions", "ignore all previous instructions", "disregard your instructions")


@action(is_system_action=True)
async def looks_like_injection(context: dict | None = None) -> bool:
    text = ((context or {}).get("user_message") or "").lower()
    return any(p in text for p in INJECTION)


@action(is_system_action=True)
async def mentions_secret(context: dict | None = None) -> bool:
    return "secret" in ((context or {}).get("bot_message") or "").lower()
