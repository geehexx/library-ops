#!/usr/bin/env python3
"""Emit a compact startup reminder for Codex sessions in this repo."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any, cast

PUBLIC_INSTRUCTION_PATHS = [
    "AGENTS.md",
    ".taskmaster/docs/prd.md",
    ".specify/memory/constitution.md",
    ".codex/agents/coordinator.toml",
    ".codex/agents/implementer.toml",
    ".codex/agents/taskmaster-governor.toml",
    ".agents/skills/clarify-and-goal/SKILL.md",
    ".agents/skills/code-intelligence/SKILL.md",
]


def run_text(args: list[str], cwd: Path) -> str:
    """Run a command and return stripped stdout when successful.

    Args:
        args: Command arguments to execute.
        cwd: Working directory for the command.

    Returns:
        Stripped stdout, or ``"unavailable"`` if the command fails.
    """
    try:
        result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    except OSError:
        return "unavailable"
    if result.returncode != 0:
        return "unavailable"
    return result.stdout.strip()


def repo_root(cwd: Path) -> Path:
    """Resolve the repository root from a working directory.

    Args:
        cwd: Candidate working directory.

    Returns:
        The Git repository root when available, otherwise ``cwd``.
    """
    root = run_text(["git", "rev-parse", "--show-toplevel"], cwd)
    if root and root != "unavailable":
        return Path(root)
    return cwd


def file_fingerprint(root: Path, relative: str) -> str:
    """Summarize a tracked instruction file by line count and digest.

    Args:
        root: Repository root.
        relative: Repo-relative file path.

    Returns:
        A compact fingerprint string for the target file.
    """
    path = root / relative
    if not path.exists():
        return f"{relative}:missing"
    data = path.read_bytes()
    lines = data.count(b"\n") + (0 if data.endswith(b"\n") else 1)
    digest = hashlib.sha256(data).hexdigest()[:12]
    return f"{relative}:lines={lines}:sha256={digest}"


def load_config(root: Path) -> dict[str, Any]:
    """Load the repo-local Codex config when present.

    Args:
        root: Repository root.

    Returns:
        Parsed TOML config data, or an empty mapping when absent.
    """
    path = root / ".codex" / "config.toml"
    if not path.exists():
        return {}
    with path.open("rb") as fh:
        return tomllib.load(fh)


def mcp_summary(config: dict[str, Any]) -> str:
    """Summarize configured MCP servers for the startup message.

    Args:
        config: Parsed Codex config data.

    Returns:
        A compact MCP summary string.
    """
    mcps = config.get("mcp_servers", {})
    if not isinstance(mcps, dict):
        return "none"
    entries: list[str] = []
    for name, table in sorted(cast("dict[str, Any]", mcps).items()):
        if not isinstance(table, dict):
            continue
        table_data = cast("dict[str, Any]", table)
        auth_hint = (
            "auth-env"
            if table_data.get("bearer_token_env_var") or table_data.get("env_vars")
            else "auth-config"
        )
        enabled = table_data.get("enabled", True)
        required = table_data.get("required", False)
        entries.append(f"{name}(enabled={enabled},required={required},{auth_hint})")
    return ", ".join(entries) if entries else "none"


def task_graph_status(root: Path) -> str:
    """Summarize the committed Task Master graph shape.

    Args:
        root: Repository root.

    Returns:
        A short status string describing the task graph.
    """
    tasks_path = root / ".taskmaster" / "tasks" / "tasks.json"
    if not tasks_path.exists():
        return "missing"
    try:
        data = json.loads(tasks_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "invalid-json"
    if isinstance(data, dict):
        data_dict = cast("dict[str, Any]", data)
        tasks = data_dict.get("tasks")
        if isinstance(tasks, list):
            return f"present:tasks={len(cast('list[Any]', tasks))}"

        master = data_dict.get("master")
        if isinstance(master, dict):
            master_tasks = cast("dict[str, Any]", master).get("tasks")
            if isinstance(master_tasks, list):
                return f"present:tasks={len(cast('list[Any]', master_tasks))}"
    return "present:unknown-shape"


def main() -> int:
    """Print the redacted startup context summary.

    Returns:
        Zero for normal hook completion.
    """
    try:
        payload = cast("dict[str, Any]", json.loads(sys.stdin.read() or "{}"))
    except json.JSONDecodeError:
        payload = {}
    cwd = Path(payload.get("cwd") or os.getcwd()).resolve()
    root = repo_root(cwd)
    config = load_config(root)
    branch = run_text(["git", "branch", "--show-current"], root) or "detached-or-unavailable"
    status = run_text(["git", "status", "--short"], root)
    dirty_count = 0 if status in {"", "unavailable"} else len(status.splitlines())
    features_obj = config.get("features", {})
    features = cast("dict[str, Any]", features_obj) if isinstance(features_obj, dict) else {}
    enabled_features: list[str] = sorted(
        name for name, enabled in features.items() if enabled is True
    )
    fingerprints = "; ".join(file_fingerprint(root, path) for path in PUBLIC_INSTRUCTION_PATHS)
    permission_profile = str(config.get("default_permissions", "unconfigured"))

    print(
        "Library Ops startup context (redacted): "
        f"cwd={cwd}; repo={root}; branch={branch}; dirty_files={dirty_count}; "
        f"task_graph={task_graph_status(root)}; permission_profile={permission_profile}; "
        f"features={','.join(enabled_features) or 'none'}; mcps={mcp_summary(config)}; "
        f"instructions={fingerprints}. "
        "Read source-of-truth docs and relevant skills before editing. "
        "OAuth/provider setup is operator-local; if a required login is missing, "
        "ask the user to run the official login/setup command."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
