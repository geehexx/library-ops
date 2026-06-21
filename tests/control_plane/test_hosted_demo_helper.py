"""Tests for the hosted demo verification helper."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_module(relative_path: str, module_name: str) -> Any:
    """Load one repo-local script module for testing."""

    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_seeded_catalog_query_requires_one_real_result() -> None:
    """Seeded hosted proof should require one exact-identifier result."""

    module = load_module("scripts/check_hosted_demo.py", "hosted_demo_helper_seeded")

    response = module.Response(
        status=200,
        url="https://example.test/catalog/?q=9780141439518",
        body=(
            '<input value="9780141439518">'
            '<div role="status">Showing 1 results for "9780141439518"</div>'
            "Matched identifier: 9780141439518"
            "Match: Exact identifier match"
        ),
    )

    checks = module.expect_catalog_query(response, "9780141439518", "seeded")

    assert [check.name for check in checks] == [
        "catalog.query_echo",
        "catalog.seeded_results",
        "catalog.exact_identifier",
    ]
    assert all(check.passed for check in checks)


def test_unseeded_provider_enabled_login_does_not_require_password_only_copy() -> None:
    """Unseeded hosts may still be truthful while exposing OAuth providers."""

    module = load_module("scripts/check_hosted_demo.py", "hosted_demo_helper_unseeded_provider")

    response = module.Response(
        status=200,
        url="https://example.test/accounts/login/",
        body=(
            "This live deployment does not have seeded demo accounts yet. Use an "
            "existing account, or refresh the demo data before treating this host as "
            "fully ready."
            "Continue with GitHub"
            "Continue with Google"
        ),
    )

    checks = module.expect_login_mode(
        response,
        "unseeded",
        "provider-enabled",
        ["github", "google"],
    )

    assert all(check.passed for check in checks)


def test_unreachable_host_returns_structured_failure_json(
    monkeypatch: Any, capsys: Any, tmp_path: Path
) -> None:
    """Main should emit a clean failure summary when the host is unreachable."""

    module = load_module("scripts/check_hosted_demo.py", "hosted_demo_helper_unreachable")

    args = SimpleNamespace(
        base_url="https://offline.example",
        mode="unseeded",
        auth_mode="password-only",
        query="9780141439518",
        expected_providers=[],
        demo_password="",
        demo_password_env="LIBRARYOPS_DEMO_ACCESS_CODE",
        roles=("librarian", "member", "admin"),
        report_file=str(tmp_path / "report.json"),
        timeout=2.0,
    )

    class FakeClient:
        def __init__(self, base_url: str, timeout: float) -> None:
            assert base_url == "https://offline.example"
            assert timeout == 2.0

        def request(
            self,
            _path: str,
            *,
            data: dict[str, str] | None = None,
            query: dict[str, str] | None = None,
            referer: str | None = None,
        ) -> Any:
            _ = (data, query, referer)
            raise RuntimeError("Request to `https://offline.example/` failed: [Errno 111] refused")

    monkeypatch.setattr(module, "parse_args", lambda: args)
    monkeypatch.setattr(module, "HostedDemoClient", FakeClient)

    exit_code = module.main()

    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["passed"] is False
    assert payload["failure_count"] == 1
    assert (
        payload["request_error"]
        == "Request to `https://offline.example/` failed: [Errno 111] refused"
    )
    assert payload["checks"][0]["name"] == "host.reachable"
    report_payload = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report_payload == payload
