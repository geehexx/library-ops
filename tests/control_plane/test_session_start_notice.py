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


def test_task_graph_status_reports_task_count_for_current_repo() -> None:
    """Ensure the startup notice reports the current Task Master graph size."""
    hook: Any = load_hook_module()

    assert hook.task_graph_status(REPO_ROOT) == "present:tasks=12"


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


def test_startup_notice_mentions_cache_safe_defaults_and_specialist_routing(
    monkeypatch: Any, capsys: Any
) -> None:
    """Ensure the startup notice advertises cache-safe defaults and delegation."""
    hook: Any = load_hook_module()
    monkeypatch.setattr(hook.sys, "stdin", StringIO(json.dumps({"cwd": str(REPO_ROOT)})))

    assert hook.main() == 0
    output = capsys.readouterr().out

    assert "approval=approve" in output
    assert "npm_config_cache=" in output
    assert "XDG_CACHE_HOME=" in output
    assert "specialist or subagent packets" in output
