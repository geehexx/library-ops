#!/usr/bin/env python3
"""Session-start and cleanup hook helpers for Serena project context."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

VALID_ACTIONS = {"activate", "cleanup"}
REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_ROOT = REPO_ROOT / ".codex" / ".runtime" / "serena-hook"


def state_path(session_id: str) -> Path:
    """Return the persisted state path for a session ID."""
    return STATE_ROOT / session_id / "tool_use_state.json"


def cleanup_state(session_id: str) -> None:
    """Remove persisted hook state for a session.

    The PreToolUse reminder path was removed, but cleanup remains so older
    runtime state from prior sessions does not accumulate indefinitely.
    """
    path = state_path(session_id).parent
    if not path.exists():
        return
    for child in path.iterdir():
        child.unlink(missing_ok=True)
    path.rmdir()


def load_payload() -> dict[str, Any] | None:
    """Load and validate the hook payload from stdin."""
    raw_input = sys.stdin.read()
    try:
        payload = json.loads(raw_input)
    except json.JSONDecodeError:
        print("Serena hook skipped: missing or invalid Codex hook JSON.", file=sys.stderr)
        return None
    if not isinstance(payload, dict) or not payload.get("session_id"):
        print("Serena hook skipped: Codex hook JSON has no session_id.", file=sys.stderr)
        return None
    return payload


def session_start_output() -> str:
    """Build the session-start reminder payload for Codex."""
    message = (
        "**IMPORTANT**: If the current directory is a coding project you are working on:"
        " 1. activate it using Serena's activate_project tool unless already done."
        " 2. if you haven't read Serena Instructions Manual yet, do so."
        " Follow this instruction before doing anything else."
    )
    return json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": message,
            }
        }
    )


def main() -> int:
    """Dispatch the Serena hook subcommands."""
    if len(sys.argv) != 2 or sys.argv[1] not in VALID_ACTIONS:
        print("usage: serena_hook.py activate|cleanup", file=sys.stderr)
        return 0

    payload = load_payload()
    if payload is None:
        return 0

    session_id = str(payload["session_id"])
    action = sys.argv[1]

    if action == "activate":
        print(session_start_output())
        return 0

    cleanup_state(session_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
