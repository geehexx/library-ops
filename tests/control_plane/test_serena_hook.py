"""Tests for the Serena session-start and cleanup hook."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from types import ModuleType

    import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK_PATH = REPO_ROOT / ".codex" / "hooks" / "serena_hook.py"


class FakeStdin:
    """Minimal stdin double for Codex hook payload tests."""

    def __init__(self, content: str) -> None:
        """Store hook payload content for later reads.

        Args:
            content: Raw hook payload content returned by ``read()``.
        """
        self.content = content

    def read(self) -> str:
        """Return the stored hook payload content."""
        return self.content


def load_hook_module() -> ModuleType:
    """Load the Serena hook module for testing."""
    spec = importlib.util.spec_from_file_location("serena_hook", HOOK_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_serena_hook_skips_invalid_json(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Ensure invalid hook JSON is ignored with a clear stderr message.

    Args:
        monkeypatch: Pytest patch helper.
        capsys: Pytest capture fixture for stderr assertions.
    """
    hook: Any = load_hook_module()

    monkeypatch.setattr(sys, "argv", ["serena_hook.py", "cleanup"])
    monkeypatch.setattr(sys, "stdin", FakeStdin("not-json"))

    assert hook.main() == 0
    assert "missing or invalid Codex hook JSON" in capsys.readouterr().err


def test_serena_hook_requires_session_id(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Ensure hook payloads without a session ID are ignored.

    Args:
        monkeypatch: Pytest patch helper.
        capsys: Pytest capture fixture for stderr assertions.
    """
    hook: Any = load_hook_module()

    monkeypatch.setattr(sys, "argv", ["serena_hook.py", "cleanup"])
    monkeypatch.setattr(sys, "stdin", FakeStdin("{}"))

    assert hook.main() == 0
    assert "no session_id" in capsys.readouterr().err


def test_serena_hook_activate_emits_session_start_context(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Ensure the activate path emits a session-start reminder.

    Args:
        monkeypatch: Pytest patch helper.
        capsys: Pytest capture fixture for stdout assertions.
    """
    hook: Any = load_hook_module()
    payload = {"session_id": "session-activate", "cwd": str(REPO_ROOT)}

    monkeypatch.setattr(sys, "argv", ["serena_hook.py", "activate"])
    monkeypatch.setattr(sys, "stdin", FakeStdin(json.dumps(payload)))

    assert hook.main() == 0
    output = json.loads(capsys.readouterr().out)
    assert output["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "activate_project" in output["hookSpecificOutput"]["additionalContext"]


def test_serena_hook_cleanup_removes_state(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Ensure cleanup removes persisted hook state for a session.

    Args:
        monkeypatch: Pytest patch helper.
        tmp_path: Temporary path used for isolated runtime state.
    """
    hook: Any = load_hook_module()
    monkeypatch.setattr(hook, "STATE_ROOT", tmp_path)
    session_id = "session-cleanup"
    state_file = hook.state_path(session_id)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text('{"stale": true}', encoding="utf-8")
    assert state_file.exists()

    payload = {"session_id": session_id}
    monkeypatch.setattr(sys, "argv", ["serena_hook.py", "cleanup"])
    monkeypatch.setattr(sys, "stdin", FakeStdin(json.dumps(payload)))
    assert hook.main() == 0
    assert not hook.state_path(session_id).exists()
