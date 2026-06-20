"""Tests for the session-stop hook."""

from __future__ import annotations

import importlib.util
import json
import sys
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from collections.abc import Mapping
    from types import ModuleType

    import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK_PATH = REPO_ROOT / ".codex" / "hooks" / "session_stop_notice.py"


def load_hook_module() -> ModuleType:
    """Load the session-stop hook module for testing."""
    spec = importlib.util.spec_from_file_location("session_stop_notice", HOOK_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def invoke_hook(
    hook: ModuleType,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    payload: Mapping[str, object],
    dirty_entries: list[str],
) -> dict[str, Any]:
    """Run the hook with controlled stdin and git status output."""

    def fake_git_status_short(_cwd: object) -> list[str]:
        return dirty_entries

    monkeypatch.setattr(hook, "git_status_short", fake_git_status_short)
    monkeypatch.setattr(sys, "stdin", StringIO(json.dumps(payload)))

    assert hook.main() == 0
    out = capsys.readouterr().out.strip()
    return cast("dict[str, Any]", json.loads(out))


def test_session_stop_notice_accepts_stop_when_worktree_clean(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Clean worktrees should return the empty JSON stop response."""
    hook = load_hook_module()
    payload = {
        "cwd": str(REPO_ROOT),
        "hook_event_name": "Stop",
        "last_assistant_message": "I have completed the refactoring.",
        "stop_hook_active": False,
    }

    result = invoke_hook(hook, capsys, monkeypatch, payload, [])

    assert result == {}


def test_session_stop_notice_emits_notice_for_dirty_worktree(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dirty worktrees should emit a notice without blocking stop requests."""
    hook = load_hook_module()
    payload = {
        "cwd": str(REPO_ROOT),
        "hook_event_name": "Stop",
        "last_assistant_message": "I have completed the refactoring.",
        "stop_hook_active": False,
    }
    result = invoke_hook(hook, capsys, monkeypatch, payload, [" M docs/example.md"])

    assert result == {"notice": "Worktree has uncommitted changes: docs/example.md."}
