"""A tool that asks before it acts (Ramen 1.0.0, MCP 2026-07-28 multi round-trip requests).

Raising `InputRequired` ends this run of the function; the worker hands the request to the client, and when the
client calls again with the user's answer the function runs again from the top with `input_responses()` filled in.
There is no session and nothing is kept on the worker between the two calls."""

from ramen_runtime import InputRequired, elicit, input_responses

NOTES = ("groceries", "ideas", "todo")  # the demo list: rebuilt on every call, so the demo can be repeated
CONFIRM = {
    "type": "object",
    "properties": {"confirm": {"type": "boolean", "title": "Delete it?", "description": "true deletes the note"}},
    "required": ["confirm"],
}


def confirm_delete(note: str) -> str:
    if note not in NOTES:
        return f"Nothing was deleted: there is no note named {note!r}. Notes: {', '.join(NOTES)}."
    answer = input_responses().get("confirm")
    if answer is None:
        raise InputRequired({"confirm": elicit(f'Delete the note "{note}"? This cannot be undone.', CONFIRM)})
    confirmed = answer.get("action") == "accept" and (answer.get("content") or {}).get("confirm") is True
    if not confirmed:
        return f'Nothing was deleted: the note "{note}" is still there.'
    remaining = [n for n in NOTES if n != note]
    return f'Deleted the note "{note}". Remaining: {", ".join(remaining)}.'
