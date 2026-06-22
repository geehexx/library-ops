"""High-signal tests for the declarative control-plane contract."""

from __future__ import annotations

import json
import shutil
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from pathlib import Path
    from types import ModuleType

from tests.control_plane._support import load_repo_module


def _checker(repo_root: Path) -> ModuleType:
    """Load the control-plane checker module."""
    return load_repo_module(
        repo_root,
        "scripts/check_control_plane.py",
        "libraryops_control_plane_checker",
    )


def _codes(issues: list[Any]) -> set[str]:
    """Collect issue codes into a set."""
    return {cast("str", issue.code) for issue in issues}


def test_current_repository_satisfies_control_plane_contract(repo_root: Path) -> None:
    """The checked-in control plane should satisfy every structural contract."""
    checker = _checker(repo_root)
    issues = checker.collect_issues(
        repo_root,
        repo_root / "tests/control_plane/contract.toml",
    )
    assert not issues, "\n".join(
        f"[{issue.code}] {issue.path}: {issue.message}" for issue in issues
    )


def test_agent_paths_are_resolved_relative_to_codex_config(
    repo_root: Path,
    tmp_path: Path,
) -> None:
    """A path that escapes .codex/agents must fail with a stable issue code."""
    checker = _checker(repo_root)
    shutil.copytree(repo_root / ".codex/agents", tmp_path / ".codex/agents")
    config = (repo_root / ".codex/config.toml").read_text(encoding="utf-8")
    config = config.replace(
        'config_file = "agents/coordinator.toml"',
        'config_file = "../coordinator.toml"',
        1,
    )
    (tmp_path / ".codex/config.toml").write_text(config, encoding="utf-8")
    contract = checker.load_contract(repo_root / "tests/control_plane/contract.toml")

    issues = checker.check_agents(tmp_path, contract)

    assert "CP106" in _codes(issues)


def test_forbidden_hook_event_is_rejected(repo_root: Path, tmp_path: Path) -> None:
    """Project policy should reject command-interception hooks by default."""
    checker = _checker(repo_root)
    (tmp_path / ".codex").mkdir()
    shutil.copy2(repo_root / ".codex/config.toml", tmp_path / ".codex/config.toml")
    shutil.copytree(repo_root / ".codex/hooks", tmp_path / ".codex/hooks")
    data = json.loads((repo_root / ".codex/hooks.json").read_text(encoding="utf-8"))
    data["hooks"]["PreToolUse"] = [
        {
            "matcher": ".*",
            "hooks": [
                {
                    "type": "command",
                    "command": "true",
                    "timeout": 1,
                }
            ],
        }
    ]
    (tmp_path / ".codex/hooks.json").write_text(
        json.dumps(data),
        encoding="utf-8",
    )
    contract = checker.load_contract(repo_root / "tests/control_plane/contract.toml")

    issues = checker.check_hooks(tmp_path, contract)

    assert "CP305" in _codes(issues)


def test_adr_index_drift_is_reported(repo_root: Path, tmp_path: Path) -> None:
    """A numbered ADR without an index row must become a visible failure."""
    checker = _checker(repo_root)
    shutil.copytree(repo_root / "docs/adr", tmp_path / "docs/adr")
    (tmp_path / "docs/adr/9999-unindexed.md").write_text(
        "# ADR-9999: Unindexed\n",
        encoding="utf-8",
    )
    contract = checker.load_contract(repo_root / "tests/control_plane/contract.toml")

    issues = checker.check_adrs(tmp_path, contract)

    assert "CP501" in _codes(issues)


def test_hidden_bidirectional_controls_are_reported(
    repo_root: Path,
    tmp_path: Path,
) -> None:
    """Security-sensitive governance text must reject invisible direction changes."""
    checker = _checker(repo_root)
    (tmp_path / "AGENTS.md").write_text("safe\u202etxt\n", encoding="utf-8")
    contract = checker.load_contract(repo_root / "tests/control_plane/contract.toml")

    issues = checker.check_bidi_controls(tmp_path, contract)

    assert "CP600" in _codes(issues)
