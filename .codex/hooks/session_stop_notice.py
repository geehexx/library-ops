"""Stop hook for Codex sessions.

The Stop hook must return valid JSON. Returning ``{}`` accepts the stop.
Returning ``{"decision": "block", "reason": "..."}`` forces a continuation.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

BLOCKER_PHRASES = (
    "blocked",
    "waiting on",
    "need user input",
    "need more info",
    "need more time",
)
HANDOFF_PHRASES = (
    "planning session",
    "handoff",
    "implementation deferred",
    "next session",
    "plan-only",
)
IMPLEMENTATION_CHECKPOINT_PHRASES = (
    "implementation checkpoint",
    "owned implementation checkpoint",
)


def load_payload() -> dict[str, Any]:
    """Load the hook payload from stdin and fall back to an empty mapping."""
    raw_input = sys.stdin.read()
    try:
        payload = json.loads(raw_input)
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    return cast("dict[str, Any]", payload)


def normalize_message(value: Any) -> str:
    """Return a lowercase string for hook-message checks."""
    if not value:
        return ""
    return str(value).strip().lower()


def contains_any(message: str, phrases: tuple[str, ...]) -> bool:
    """Check whether any tracked phrase appears in the message."""
    return any(phrase in message for phrase in phrases)


def git_status_short(cwd: Path) -> list[str]:
    """Return the short git-status lines for the repository root."""
    try:
        completed = subprocess.run(
            ["git", "status", "--short"],
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return []
    if completed.returncode != 0:
        return []
    return [line for line in completed.stdout.splitlines() if line.strip()]


def build_block_reason(dirty_entries: list[str]) -> str:
    """Build the continuation reason for a dirty worktree."""
    preview = ", ".join(dirty_entries[:3])
    if preview:
        return (
            "Worktree still has uncommitted changes: "
            f"{preview}. Run validation or explain the remaining work before stopping."
        )
    return (
        "Worktree still has uncommitted changes. Run validation or explain "
        "the remaining work before stopping."
    )


def should_block_stop(payload: dict[str, Any], dirty_entries: list[str]) -> str | None:
    """Return a continuation reason when the stop request should be blocked."""
    if payload.get("stop_hook_active"):
        return None
    if not dirty_entries:
        return None

    message = normalize_message(payload.get("last_assistant_message"))
    if contains_any(message, BLOCKER_PHRASES):
        return None
    if contains_any(message, HANDOFF_PHRASES):
        return None
    if contains_any(message, IMPLEMENTATION_CHECKPOINT_PHRASES):
        return None
    return build_block_reason(dirty_entries)


def emit_json(payload: dict[str, Any]) -> int:
    """Print a JSON response and exit cleanly."""
    print(json.dumps(payload))
    return 0


def main() -> int:
    """Decide whether Codex should stop or continue."""
    payload = load_payload()
    cwd = Path(payload.get("cwd") or os.getcwd()).resolve()
    dirty_entries = git_status_short(cwd)
    block_reason = should_block_stop(payload, dirty_entries)
    if block_reason is not None:
        return emit_json({"decision": "block", "reason": block_reason})
    return emit_json({})


if __name__ == "__main__":
    raise SystemExit(main())
