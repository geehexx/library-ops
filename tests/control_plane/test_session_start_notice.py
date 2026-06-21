"""Tests for the startup notice Codex hook."""

from __future__ import annotations

import importlib.util
import json
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK_PATH = REPO_ROOT / ".codex" / "hooks" / "session_start_notice.py"


def load_hook_module() -> ModuleType:
    """Load the startup notice hook module for testing."""
    spec = importlib.util.spec_from_file_location("session_start_notice", HOOK_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_task_graph_status_reports_present_task_graph_for_current_repo() -> None:
    """Ensure the startup notice reports that the Task Master graph is present."""
    hook: Any = load_hook_module()

    assert hook.task_graph_status(REPO_ROOT).startswith("present:tasks=")


def test_mcp_summary_mentions_required_servers() -> None:
    """Ensure the startup notice mentions required MCP servers."""
    hook: Any = load_hook_module()
    config = hook.load_config(REPO_ROOT)

    summary = hook.mcp_summary(config)

    assert "context7(" in summary
    assert "exa(" in summary
    assert "taskmaster-ai(" in summary
    assert "code-review-graph(" in summary
    assert "serena(" in summary


def test_startup_notice_mentions_cache_safe_defaults_and_spark_lanes(
    monkeypatch: Any, capsys: Any
) -> None:
    """Ensure the startup notice advertises cache-safe defaults and Spark lanes."""
    hook: Any = load_hook_module()
    monkeypatch.setattr(hook.sys, "stdin", StringIO(json.dumps({"cwd": str(REPO_ROOT)})))

    assert hook.main() == 0
    output = capsys.readouterr().out

    for expected_fragment in (
        "approval=approve",
        "npm_config_cache=",
        "XDG_CACHE_HOME=",
        "command_runner",
        "context_gatherer",
        "debugger",
        "single_file_implementer",
        "implementer",
        "multiple turns",
        "stop hook emits JSON only",
        "/mnt/c/...",
        "parse-prd --force",
    ):
        assert expected_fragment in output


def test_resume_notice_is_more_compact_and_continuation_focused(
    monkeypatch: Any, capsys: Any
) -> None:
    """Ensure the resume notice is shorter and centered on continuation context."""
    hook: Any = load_hook_module()
    payload = {
        "cwd": str(REPO_ROOT),
        "hook_event_name": "resume",
    }
    monkeypatch.setattr(hook.sys, "stdin", StringIO(json.dumps(payload)))

    assert hook.main() == 0
    output = capsys.readouterr().out

    assert "resume context" in output
    assert "continuation=.codex-session-notes/continuation.md" in output
    assert "instructions=" not in output
    assert "cache_hint=" not in output
    assert "mcps=" not in output
