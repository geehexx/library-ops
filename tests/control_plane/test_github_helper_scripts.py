"""Regression tests for GitHub review helper scripts."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_module(relative_path: str, module_name: str) -> Any:
    """Load a script file as an importable module for testing.

    Args:
        relative_path: Repo-relative path to the script file.
        module_name: Synthetic module name used for loading.

    Returns:
        The loaded module object.
    """
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fetch_checks_accepts_pending_exit_code_with_json_stdout(
    tmp_path: Path,
) -> None:
    """Ensure pending `gh pr checks` output is still parsed.

    Args:
        tmp_path: Temporary path used as the fake repo root.
    """
    module = load_module(
        ".agents/skills/gh-fix-ci/scripts/inspect_pr_checks.py",
        "inspect_pr_checks_pending",
    )

    def fake_run_gh_command(args: list[str], cwd: Path) -> Any:
        assert args[:3] == ["pr", "checks", "123"]
        assert cwd == tmp_path
        return module.GhResult(
            8,
            '[{"name":"quality","state":"pending","conclusion":"","detailsUrl":"https://example.com"}]',
            "",
        )

    module.run_gh_command = fake_run_gh_command

    checks = module.fetch_checks("123", tmp_path)

    assert checks == [
        {
            "name": "quality",
            "state": "pending",
            "conclusion": "",
            "detailsUrl": "https://example.com",
        }
    ]


def test_fetch_comments_routes_gh_cache_into_tmp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure PR comment fetching relocates gh cache writes away from home."""
    module = load_module(
        ".agents/skills/gh-address-comments/scripts/fetch_comments.py",
        "fetch_comments_cache_env",
    )
    captured: dict[str, Any] = {}

    def fake_run(
        cmd: list[str],
        **kwargs: Any,
    ) -> Any:
        captured["cmd"] = cmd
        captured["env"] = kwargs.get("env")
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    assert module._run(["gh", "auth", "status"]) == "ok"
    assert captured["cmd"] == ["gh", "auth", "status"]
    assert str(captured["env"]["XDG_CACHE_HOME"]).endswith("codex-gh-cache")


def test_fetch_checks_fails_without_stdout_on_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Ensure a hard `gh pr checks` failure still reports an error.

    Args:
        tmp_path: Temporary path used as the fake repo root.
        capsys: Pytest capture fixture for stderr assertions.
    """
    module = load_module(
        ".agents/skills/gh-fix-ci/scripts/inspect_pr_checks.py",
        "inspect_pr_checks_error",
    )

    def fake_run_gh_command(_args: list[str], cwd: Path) -> Any:
        assert cwd == tmp_path
        return module.GhResult(1, "", "boom")

    module.run_gh_command = fake_run_gh_command

    checks = module.fetch_checks("123", tmp_path)

    assert checks is None
    assert "boom" in capsys.readouterr().err


def test_inspect_pr_checks_routes_gh_cache_into_tmp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure the failing-check inspector relocates gh cache writes away from home."""
    module = load_module(
        ".agents/skills/gh-fix-ci/scripts/inspect_pr_checks.py",
        "inspect_pr_checks_cache_env",
    )
    captured: dict[str, Any] = {}

    def fake_run(
        args: list[str],
        cwd: Path,
        **kwargs: Any,
    ) -> Any:
        captured["args"] = args
        captured["cwd"] = cwd
        captured["env"] = kwargs.get("env")
        return SimpleNamespace(returncode=0, stdout="{}", stderr="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    result = module.run_gh_command(["auth", "status"], Path("."))

    assert result.returncode == 0
    assert captured["args"] == ["gh", "auth", "status"]
    assert str(captured["env"]["XDG_CACHE_HOME"]).endswith("codex-gh-cache")


def test_get_current_pr_ref_uses_base_repository() -> None:
    """Ensure PR comment fetching resolves the base repository slug."""
    module = load_module(
        ".agents/skills/gh-address-comments/scripts/fetch_comments.py",
        "fetch_comments_base_repo",
    )

    def fake_pr_view_json(fields: str) -> dict[str, int]:
        assert fields == "number"
        return {
            "number": 7,
        }

    def fake_repo_view_json(fields: str) -> dict[str, str]:
        assert fields == "nameWithOwner"
        return {"nameWithOwner": "base-owner/base-repo"}

    module.gh_pr_view_json = fake_pr_view_json
    module.gh_repo_view_json = fake_repo_view_json

    owner, repo, number = module.get_current_pr_ref()

    assert (owner, repo, number) == ("base-owner", "base-repo", 7)


def test_fetch_all_deduplicates_exhausted_connections(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure pagination does not duplicate exhausted conversation pages.

    Args:
        monkeypatch: Pytest patch helper for replacing the GraphQL function.
    """
    module = load_module(
        ".agents/skills/gh-address-comments/scripts/fetch_comments.py",
        "fetch_comments_pagination",
    )

    responses = [
        {
            "data": {
                "repository": {
                    "pullRequest": {
                        "number": 7,
                        "url": "https://github.com/base-owner/base-repo/pull/7",
                        "title": "Title",
                        "state": "OPEN",
                        "comments": {
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                            "nodes": [{"id": "c1", "body": "first"}],
                        },
                        "reviews": {
                            "pageInfo": {"hasNextPage": True, "endCursor": "reviews-2"},
                            "nodes": [{"id": "r1", "body": "review-1"}],
                        },
                        "reviewThreads": {
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                            "nodes": [{"id": "t1", "path": "a.py"}],
                        },
                    }
                }
            }
        },
        {
            "data": {
                "repository": {
                    "pullRequest": {
                        "number": 7,
                        "url": "https://github.com/base-owner/base-repo/pull/7",
                        "title": "Title",
                        "state": "OPEN",
                        "comments": {
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                            "nodes": [{"id": "c1", "body": "first"}],
                        },
                        "reviews": {
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                            "nodes": [{"id": "r2", "body": "review-2"}],
                        },
                        "reviewThreads": {
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                            "nodes": [{"id": "t1", "path": "a.py"}],
                        },
                    }
                }
            }
        },
    ]

    def fake_graphql(
        owner: str,
        repo: str,
        number: int,
        comments_cursor: str | None = None,
        reviews_cursor: str | None = None,
        threads_cursor: str | None = None,
    ) -> Any:
        assert owner == "base-owner"
        assert repo == "base-repo"
        assert number == 7
        if reviews_cursor is None:
            assert comments_cursor is None
            assert threads_cursor is None
        return responses.pop(0)

    monkeypatch.setattr(module, "gh_api_graphql", fake_graphql)

    result = module.fetch_all("base-owner", "base-repo", 7)

    assert [comment["id"] for comment in result["conversation_comments"]] == ["c1"]
    assert [review["id"] for review in result["reviews"]] == ["r1", "r2"]
    assert [thread["id"] for thread in result["review_threads"]] == ["t1"]
