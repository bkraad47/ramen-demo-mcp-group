"""A long-running tool (Ramen 1.0.0): `"task": true` in the proto lets a client that declared the MCP tasks
extension get a task id at once and poll for the result; everyone else waits for the answer as usual. `progress()`
does nothing unless the client asked for progress."""

import time

from ramen_runtime import progress

MAX_SECONDS = 30


def report(seconds: int) -> str:
    seconds = max(0, min(int(seconds), MAX_SECONDS))
    for done in range(seconds):
        progress(done, total=seconds, message=f"section {done + 1} of {seconds}")
        time.sleep(1)
    progress(seconds, total=seconds, message="report ready")
    return f"Report ready after {seconds} s."
