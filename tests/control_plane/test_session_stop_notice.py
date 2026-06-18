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


def test_session_stop_notice_blocks_dirty_completion_without_validation(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dirty worktrees should force continuation when validation is missing."""
    hook = load_hook_module()
    payload = {
        "cwd": str(REPO_ROOT),
        "hook_event_name": "Stop",
        "last_assistant_message": "I have completed the refactoring.",
        "stop_hook_active": False,
    }

    result = invoke_hook(
        hook,
        capsys,
        monkeypatch,
        payload,
        [
            " M .codex/hooks/session_stop_notice.py",
            " M tests/control_plane/test_session_stop_notice.py",
        ],
    )

    assert result["decision"] == "block"
    reason = str(result["reason"])
    assert "uncommitted changes" in reason
    assert "validation" in reason


def test_session_stop_notice_accepts_dirty_worktree_when_validation_is_reported(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reported validation evidence should allow the stop to proceed."""
    hook = load_hook_module()
    payload = {
        "cwd": str(REPO_ROOT),
        "hook_event_name": "Stop",
        "last_assistant_message": "Tests passed and the changes are validated.",
        "stop_hook_active": False,
    }

    result = invoke_hook(
        hook,
        capsys,
        monkeypatch,
        payload,
        [" M .codex/hooks/session_stop_notice.py"],
    )

    assert result == {}


def test_session_stop_notice_accepts_after_forced_continuation(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The hook should not re-block after it has already forced continuation."""
    hook = load_hook_module()
    payload = {
        "cwd": str(REPO_ROOT),
        "hook_event_name": "Stop",
        "last_assistant_message": "I have completed the refactoring.",
        "stop_hook_active": True,
    }

    result = invoke_hook(
        hook,
        capsys,
        monkeypatch,
        payload,
        [" M .codex/hooks/session_stop_notice.py"],
    )

    assert result == {}
