"""Tests for the startup notice Codex hook."""

from __future__ import annotations

import importlib.util
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
