#!/usr/bin/env python3
"""Validate hosted Library Ops demo surfaces for release evidence."""

from __future__ import annotations

import argparse
import html
import http.cookiejar
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from typing import Final

DEFAULT_BASE_URL: Final[str] = "https://library-ops.onrender.com"
DEFAULT_QUERY: Final[str] = "9780141439518"
DEFAULT_PASSWORD_ENV: Final[str] = "LIBRARYOPS_DEMO_ACCESS_CODE"
AUTH_MODES: Final[tuple[str, ...]] = ("password-only", "provider-enabled")

ROLE_EMAILS: Final[dict[str, str]] = {
    "librarian": "librarian@libraryops.demo",
    "member": "member@libraryops.demo",
    "admin": "admin@libraryops.demo",
}

EXPECTED_ROLE_LABELS: Final[dict[str, str]] = {
    "librarian": "Librarian",
    "member": "Member",
    "admin": "Admin",
}
PROVIDER_LABELS: Final[dict[str, str]] = {
    "google": "Google",
    "github": "GitHub",
}


@dataclass(slots=True)
class Response:
    """HTTP response details needed for verification."""

    status: int
    url: str
    body: str


@dataclass(slots=True)
class CheckResult:
    """One pass/fail verification record."""

    name: str
    passed: bool
    detail: str
    url: str


class HostedDemoClient:
    """Fetch and submit hosted demo routes with cookie support."""

    def __init__(self, base_url: str, timeout: float) -> None:
        """Configure the client for one base URL."""

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

    def request(
        self,
        path: str,
        *,
        data: dict[str, str] | None = None,
        query: dict[str, str] | None = None,
        referer: str | None = None,
    ) -> Response:
        """Perform one GET or form POST request."""

        url = f"{self.base_url}{path}"
        if query:
            url = f"{url}?{urllib.parse.urlencode(query)}"
        headers = {
            "User-Agent": "library-ops-hosted-check/1.0",
        }
        payload: bytes | None = None
        if data is not None:
            payload = urllib.parse.urlencode(data).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        if referer is not None:
            headers["Referer"] = referer
        request = urllib.request.Request(url, data=payload, headers=headers)
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8", errors="replace")
                return Response(
                    status=response.status,
                    url=str(response.url),
                    body=body,
                )
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            return Response(
                status=error.code,
                url=str(error.url),
                body=body,
            )
        except urllib.error.URLError as error:
            reason = getattr(error, "reason", error)
            raise RuntimeError(f"Request to `{url}` failed: {reason}") from error

    def login(self, email: str, password: str) -> Response:
        """Sign in through the hosted login form."""

        login_page = self.request("/accounts/login/")
        csrf_token = extract_input_value(login_page.body, "csrfmiddlewaretoken")
        return self.request(
            "/accounts/login/",
            data={
                "csrfmiddlewaretoken": csrf_token,
                "login": email,
                "password": password,
                "remember": "on",
            },
            referer=login_page.url,
        )


def extract_input_value(body: str, name: str) -> str:
    """Return the HTML input value for one field name."""

    pattern = re.compile(
        rf'name="{re.escape(name)}"[^>]*value="([^"]+)"',
        re.IGNORECASE,
    )
    match = pattern.search(body)
    if match is None:
        raise ValueError(f"Could not find input `{name}` in the HTML response.")
    return html.unescape(match.group(1))


def metric_value(body: str, label: str) -> int:
    """Extract one integer home-page metric by eyebrow label."""

    pattern = re.compile(
        rf"<p class=\"eyebrow\">{re.escape(label)}</p>\s*<p class=\"metric-value\">(\d+)</p>",
        re.MULTILINE,
    )
    match = pattern.search(body)
    if match is None:
        raise ValueError(f"Could not find metric `{label}` in the HTML response.")
    return int(match.group(1))


def contains(body: str, text: str) -> bool:
    """Return whether the response body contains the target text."""

    return text in body


def build_check(name: str, passed: bool, detail: str, url: str) -> CheckResult:
    """Construct one result row."""

    return CheckResult(name=name, passed=passed, detail=detail, url=url)


def expect_home_mode(response: Response, mode: str) -> list[CheckResult]:
    """Validate the public home page for the requested hosted state."""

    checks: list[CheckResult] = []
    work_count = metric_value(response.body, "Catalog works")
    copy_count = metric_value(response.body, "Inventory copies")
    if mode == "seeded":
        checks.append(
            build_check(
                name="home.seeded_counts",
                passed=work_count > 0 and copy_count > 0,
                detail=f"Catalog works={work_count}, inventory copies={copy_count}.",
                url=response.url,
            )
        )
        checks.append(
            build_check(
                name="home.seeded_copy",
                passed=contains(
                    response.body,
                    "Explore a server-rendered library workflow with seeded catalog",
                )
                and not contains(response.body, "environment is currently unseeded."),
                detail="Expected seeded demo copy and absence of the unseeded warning.",
                url=response.url,
            )
        )
    else:
        checks.append(
            build_check(
                name="home.unseeded_counts",
                passed=work_count == 0 and copy_count == 0,
                detail=f"Catalog works={work_count}, inventory copies={copy_count}.",
                url=response.url,
            )
        )
        checks.append(
            build_check(
                name="home.unseeded_copy",
                passed=contains(
                    response.body,
                    "demo data and accounts need an operator refresh",
                )
                and contains(response.body, "environment is currently unseeded."),
                detail="Expected explicit unseeded demo/operator-refresh copy.",
                url=response.url,
            )
        )
    return checks


def expect_login_mode(
    response: Response,
    mode: str,
    auth_mode: str,
    expected_providers: list[str],
) -> list[CheckResult]:
    """Validate the public login page and optional provider links."""

    checks: list[CheckResult] = []
    if mode == "seeded":
        checks.append(
            build_check(
                name="login.seeded_copy",
                passed=contains(
                    response.body,
                    "Use a seeded demo account for the guided product tour",
                ),
                detail="Expected seeded demo login guidance.",
                url=response.url,
            )
        )
    else:
        checks.append(
            build_check(
                name="login.unseeded_copy",
                passed=contains(
                    response.body,
                    "This live deployment does not have seeded demo accounts yet",
                ),
                detail="Expected truthful unseeded demo-account guidance.",
                url=response.url,
            )
        )
        if auth_mode == "password-only":
            checks.append(
                build_check(
                    name="login.password_only_fallback",
                    passed=contains(
                        response.body,
                        "This deployment exposes password sign-in only.",
                    ),
                    detail="Expected the password-only fallback guidance.",
                    url=response.url,
                )
            )
        else:
            checks.append(
                build_check(
                    name="login.provider_enabled",
                    passed=not contains(
                        response.body,
                        "This deployment exposes password sign-in only.",
                    ),
                    detail="Expected provider-enabled login without the password-only fallback.",
                    url=response.url,
                )
            )
    for provider in expected_providers:
        label = f"Continue with {PROVIDER_LABELS.get(provider, provider.title())}"
        checks.append(
            build_check(
                name=f"login.provider.{provider}",
                passed=contains(response.body, label),
                detail=f"Expected visible provider link `{label}`.",
                url=response.url,
            )
        )
    return checks


def expect_catalog_query(response: Response, query: str, mode: str) -> list[CheckResult]:
    """Validate the hosted catalog query surface."""

    checks: list[CheckResult] = [
        build_check(
            name="catalog.query_echo",
            passed=contains(response.body, f'value="{query}"'),
            detail=f"Expected the query field to echo `{query}`.",
            url=response.url,
        )
    ]
    if mode == "seeded":
        result_match = re.search(
            rf'Showing (\d+) results? for "{re.escape(query)}"',
            response.body,
        )
        result_count = int(result_match.group(1)) if result_match else 0
        checks.append(
            build_check(
                name="catalog.seeded_results",
                passed=result_count == 1,
                detail=f"Observed result count for `{query}`: {result_count}.",
                url=response.url,
            )
        )
        checks.append(
            build_check(
                name="catalog.exact_identifier",
                passed=contains(response.body, f"Matched identifier: {query}")
                and contains(response.body, "Match: Exact identifier match"),
                detail="Expected exact-identifier result-card copy.",
                url=response.url,
            )
        )
    else:
        checks.append(
            build_check(
                name="catalog.unseeded_results",
                passed=contains(response.body, f'Showing 0 results for "{query}"'),
                detail="Expected zero results before the hosted demo refresh runs.",
                url=response.url,
            )
        )
    return checks


def expect_role_login(
    *,
    base_url: str,
    timeout: float,
    role: str,
    password: str,
) -> list[CheckResult]:
    """Validate the role-aware seeded flows for one demo user."""

    client = HostedDemoClient(base_url=base_url, timeout=timeout)
    login_response = client.login(ROLE_EMAILS[role], password)
    checks: list[CheckResult] = [
        build_check(
            name=f"auth.{role}.login_redirect",
            passed=login_response.status == 200 and login_response.url.rstrip("/") == base_url.rstrip("/"),
            detail=f"Final login URL was `{login_response.url}` with status {login_response.status}.",
            url=login_response.url,
        ),
        build_check(
            name=f"auth.{role}.signed_in_label",
            passed=contains(login_response.body, ROLE_EMAILS[role])
            and contains(login_response.body, f"({EXPECTED_ROLE_LABELS[role]})"),
            detail=f"Expected signed-in home surface for `{ROLE_EMAILS[role]}`.",
            url=login_response.url,
        ),
    ]
    if role in {"librarian", "member"}:
        circulation_response = client.request("/circulation/")
        checks.extend(
            [
                build_check(
                    name=f"circulation.{role}.dashboard",
                    passed=circulation_response.status == 200
                    and contains(circulation_response.body, "Circulation Dashboard"),
                    detail="Expected the circulation dashboard to be reachable.",
                    url=circulation_response.url,
                ),
                build_check(
                    name=f"circulation.{role}.seed_snapshot",
                    passed=all(
                        contains(circulation_response.body, expected)
                        for expected in (
                            "Visible loans: 3",
                            "Active: 2",
                            "Overdue: 1",
                            "Recent returns: 1",
                            "CIRC-DEMO-001",
                            "CIRC-DEMO-002",
                            "CIRC-DEMO-003",
                        )
                    ),
                    detail="Expected the seeded active, overdue, and returned circulation snapshot.",
                    url=circulation_response.url,
                ),
            ]
        )
    if role == "librarian":
        create_response = client.request("/catalog/create/")
        checks.append(
            build_check(
                name="catalog.librarian_create_access",
                passed=create_response.status == 200,
                detail=f"Expected librarian access to `/catalog/create/`, got {create_response.status}.",
                url=create_response.url,
            )
        )
    if role == "member":
        create_response = client.request("/catalog/create/")
        checks.append(
            build_check(
                name="catalog.member_create_denied",
                passed=create_response.status == 403
                and contains(create_response.body, "Access denied"),
                detail=f"Expected member denial on `/catalog/create/`, got {create_response.status}.",
                url=create_response.url,
            )
        )
    if role == "admin":
        admin_response = client.request("/admin/")
        checks.append(
            build_check(
                name="admin.admin_index",
                passed=admin_response.status == 200
                and admin_response.url.rstrip("/").endswith("/admin"),
                detail=f"Expected admin index reachability, got {admin_response.status}.",
                url=admin_response.url,
            )
        )
    return checks


def parse_args() -> argparse.Namespace:
    """Parse the CLI options."""

    parser = argparse.ArgumentParser(
        description=(
            "Validate the hosted Library Ops surfaces for the current unseeded "
            "or post-refresh seeded state."
        )
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Hosted base URL to validate.")
    parser.add_argument(
        "--mode",
        choices=("seeded", "unseeded"),
        required=True,
        help="Hosted state expected for this validation run.",
    )
    parser.add_argument(
        "--auth-mode",
        choices=AUTH_MODES,
        default="password-only",
        help="Expected login-surface auth posture for the target host.",
    )
    parser.add_argument(
        "--query",
        default=DEFAULT_QUERY,
        help="Catalog query used for exact-identifier proof.",
    )
    parser.add_argument(
        "--expect-provider",
        dest="expected_providers",
        action="append",
        choices=("google", "github"),
        default=[],
        help="Assert that the login page shows the given provider link.",
    )
    parser.add_argument(
        "--demo-password",
        default="",
        help="Seeded demo password. When provided, role-aware seeded checks run too.",
    )
    parser.add_argument(
        "--demo-password-env",
        default=DEFAULT_PASSWORD_ENV,
        help="Environment variable used when --demo-password is not provided.",
    )
    parser.add_argument(
        "--roles",
        nargs="+",
        choices=tuple(ROLE_EMAILS),
        default=("librarian", "member", "admin"),
        help="Seeded role flows to validate when a demo password is available.",
    )
    parser.add_argument(
        "--report-file",
        default="",
        help="Optional path for a JSON report.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Per-request timeout in seconds.",
    )
    return parser.parse_args()


def main() -> int:
    """Run the hosted verification pass."""

    args = parse_args()
    base_url = args.base_url.rstrip("/")
    password = args.demo_password or os.getenv(args.demo_password_env, "").strip()
    client = HostedDemoClient(base_url=base_url, timeout=args.timeout)

    checks: list[CheckResult] = []
    request_error = ""
    try:
        home_response = client.request("/")
        checks.extend(expect_home_mode(home_response, args.mode))

        login_response = client.request("/accounts/login/")
        checks.extend(
            expect_login_mode(
                login_response,
                args.mode,
                args.auth_mode,
                args.expected_providers,
            )
        )

        catalog_response = client.request("/catalog/", query={"q": args.query})
        checks.extend(expect_catalog_query(catalog_response, args.query, args.mode))

        if args.mode == "seeded" and password:
            for role in args.roles:
                checks.extend(
                    expect_role_login(
                        base_url=base_url,
                        timeout=args.timeout,
                        role=role,
                        password=password,
                    )
                )
        elif args.mode == "seeded":
            checks.append(
                build_check(
                    name="seeded.role_checks_skipped",
                    passed=False,
                    detail=(
                        "Seeded mode was requested without a demo password; role-aware checks were skipped. "
                        "Provide --demo-password or set the configured password env var."
                    ),
                    url=f"{base_url}/accounts/login/",
                )
            )
    except RuntimeError as error:
        request_error = str(error)
        checks.append(
            build_check(
                name="host.reachable",
                passed=False,
                detail=request_error,
                url=base_url,
            )
        )

    failures = [check for check in checks if not check.passed]
    summary = {
        "base_url": base_url,
        "mode": args.mode,
        "auth_mode": args.auth_mode,
        "query": args.query,
        "expected_providers": args.expected_providers,
        "checks": [asdict(check) for check in checks],
        "passed": not failures,
        "failure_count": len(failures),
        "request_error": request_error or None,
    }
    if args.report_file:
        report_path = Path(args.report_file)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2)
            handle.write("\n")
    json.dump(summary, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
