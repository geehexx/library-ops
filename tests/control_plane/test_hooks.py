"""Protocol-level tests for the repo-owned Codex lifecycle hooks."""

from __future__ import annotations

import io
import json
import sys
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from pathlib import Path
    from types import ModuleType

    import pytest

from tests.control_plane._support import load_repo_module


def _invoke(
    module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    payload: dict[str, Any] | str,
    argv: list[str] | None = None,
) -> tuple[int, str, str]:
    """Run the hook entrypoint and capture its output."""
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    monkeypatch.setattr(sys, "stdin", io.StringIO(raw))
    if argv is not None:
        monkeypatch.setattr(sys, "argv", argv)
    result = cast("int", module.main())
    captured = capsys.readouterr()
    return result, captured.out.strip(), captured.err.strip()


def test_stop_hook_accepts_clean_worktree_with_empty_json(
    repo_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A clean worktree should never block a Codex stop."""
    module = load_repo_module(
        repo_root,
        ".codex/hooks/session_stop_notice.py",
        "libraryops_session_stop_clean",
    )

    def clean_status(_cwd: object) -> list[str]:
        return []

    monkeypatch.setattr(module, "git_status_short", clean_status)

    result, stdout, _stderr = _invoke(
        module,
        monkeypatch,
        capsys,
        {"cwd": str(repo_root)},
    )

    assert result == 0
    assert json.loads(stdout) == {}


def test_stop_hook_dirty_notice_remains_advisory(
    repo_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Dirty state may produce a notice, but never a blocking stop decision."""
    module = load_repo_module(
        repo_root,
        ".codex/hooks/session_stop_notice.py",
        "libraryops_session_stop_dirty",
    )

    def dirty_status(_cwd: object) -> list[str]:
        return [" M README.md"]

    monkeypatch.setattr(module, "git_status_short", dirty_status)

    result, stdout, _stderr = _invoke(
        module,
        monkeypatch,
        capsys,
        {"cwd": str(repo_root)},
    )
    response = json.loads(stdout)

    assert result == 0
    assert isinstance(response.get("systemMessage"), str)
    assert response["systemMessage"].strip()
    assert response.get("decision") != "block"
    assert response.get("continue") is not False


def test_serena_activate_emits_valid_session_start_json(
    repo_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Activation output must remain valid JSON accepted by SessionStart."""
    module = load_repo_module(
        repo_root,
        ".codex/hooks/serena_hook.py",
        "libraryops_serena_activate",
    )
    monkeypatch.setattr(module, "STATE_ROOT", tmp_path)

    result, stdout, _stderr = _invoke(
        module,
        monkeypatch,
        capsys,
        {"session_id": "session-1", "cwd": str(repo_root)},
        ["serena_hook.py", "activate"],
    )
    response = json.loads(stdout)

    assert result == 0
    assert isinstance(response, dict)
    assert response


def test_serena_cleanup_removes_session_state(
    repo_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Cleanup must remove only the state file for the current session."""
    module = load_repo_module(
        repo_root,
        ".codex/hooks/serena_hook.py",
        "libraryops_serena_cleanup",
    )
    monkeypatch.setattr(module, "STATE_ROOT", tmp_path)
    state_path = cast("Path", module.state_path("session-2"))
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text("active\n", encoding="utf-8")

    result, stdout, _stderr = _invoke(
        module,
        monkeypatch,
        capsys,
        {"session_id": "session-2", "cwd": str(repo_root)},
        ["serena_hook.py", "cleanup"],
    )

    assert result == 0
    assert not state_path.exists()
    if stdout:
        assert isinstance(json.loads(stdout), dict)


def test_serena_invalid_payload_fails_open(
    repo_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Malformed hook input must not crash or block the Codex lifecycle."""
    module = load_repo_module(
        repo_root,
        ".codex/hooks/serena_hook.py",
        "libraryops_serena_invalid",
    )
    monkeypatch.setattr(module, "STATE_ROOT", tmp_path)

    result, stdout, _stderr = _invoke(
        module,
        monkeypatch,
        capsys,
        "{not-json",
        ["serena_hook.py", "activate"],
    )

    assert result == 0
    if stdout:
        assert isinstance(json.loads(stdout), dict)


def test_session_start_reports_required_mcps(
    repo_root: Path,
) -> None:
    """The startup notice should derive required MCP names from current config."""
    module = load_repo_module(
        repo_root,
        ".codex/hooks/session_start_notice.py",
        "libraryops_session_start_config",
    )
    config = cast("dict[str, Any]", module.load_config(repo_root))
    servers_value = config.get("mcp_servers", {})
    assert isinstance(servers_value, dict)
    servers = cast("dict[str, Any]", servers_value)
    required: set[str] = set()
    for name, settings_value in servers.items():
        if not isinstance(settings_value, dict):
            continue
        settings = cast("dict[str, Any]", settings_value)
        if settings.get("required") is True:
            required.add(name)

    summary = cast("str", module.mcp_summary(config))

    assert required
    for name in required:
        assert name in summary


def test_session_start_main_emits_bounded_non_secret_output(
    repo_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Startup output should be useful, bounded, and avoid credential values."""
    module = load_repo_module(
        repo_root,
        ".codex/hooks/session_start_notice.py",
        "libraryops_session_start_main",
    )

    result, stdout, _stderr = _invoke(
        module,
        monkeypatch,
        capsys,
        {"source": "startup", "cwd": str(repo_root)},
    )

    assert result == 0
    assert stdout
    assert len(stdout) < 12_000
    assert "OPENAI_API_KEY=" not in stdout
    assert "EXA_API_KEY=" not in stdout
    assert "RENDER_API_KEY=" not in stdout
