#!/usr/bin/env python3
"""Stop hook for Codex sessions.

The Stop hook must return valid JSON. Returning ``{}`` accepts the stop.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, cast


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


def build_notice(dirty_entries: list[str]) -> str:
    """Build a lightweight notice for a dirty worktree."""
    preview = ", ".join(
        entry[3:].strip() if len(entry) > 3 else entry.strip() for entry in dirty_entries[:3]
    )
    if preview:
        return f"Worktree has uncommitted changes: {preview}."
    return "Worktree has uncommitted changes."


def emit_json(payload: dict[str, Any]) -> int:
    """Print a JSON response and exit cleanly."""
    print(json.dumps(payload))
    return 0


def main() -> int:
    """Emit a lightweight dirty-worktree notice, if needed."""
    payload = load_payload()
    cwd = Path(payload.get("cwd") or os.getcwd()).resolve()
    dirty_entries = git_status_short(cwd)
    if dirty_entries:
        return emit_json({"notice": build_notice(dirty_entries)})
    return emit_json({})


if __name__ == "__main__":
    raise SystemExit(main())
