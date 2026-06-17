"""Global pytest guards and fixtures for the repo test tree."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
ALLOWED_TEST_KIND_DIRS = {
    "control_plane",
    "e2e",
    "integration",
    "property",
    "smoke",
    "unit",
}


def pytest_sessionstart(session: pytest.Session) -> None:
    """Fail fast if product tests reappear under `src/libraryops`.

    Args:
        session: The active pytest session.

    Raises:
        pytest.UsageError: Test files appear under `src/libraryops/` or
            outside the allowed kind-first test buckets.
    """

    del session
    offenders = sorted(
        path.relative_to(REPO_ROOT).as_posix()
        for path in (REPO_ROOT / "src" / "libraryops").rglob("test_*.py")
    )
    offenders.extend(
        sorted(
            path.relative_to(REPO_ROOT).as_posix()
            for path in (REPO_ROOT / "src" / "libraryops").rglob("*_test.py")
        )
    )
    if offenders:
        joined = "\n".join(offenders)
        raise pytest.UsageError(
            "Product tests must live under tests/, not src/libraryops/.\n"
            f"Offending paths:\n{joined}"
        )

    test_root = REPO_ROOT / "tests"
    misplaced_tests = sorted(
        path.relative_to(test_root).as_posix()
        for path in test_root.rglob("test_*.py")
        if path.relative_to(test_root).parts[0] not in ALLOWED_TEST_KIND_DIRS
    )
    misplaced_tests.extend(
        sorted(
            path.relative_to(test_root).as_posix()
            for path in test_root.rglob("*_test.py")
            if path.relative_to(test_root).parts[0] not in ALLOWED_TEST_KIND_DIRS
        )
    )
    if misplaced_tests:
        joined = "\n".join(misplaced_tests)
        allowed = ", ".join(sorted(ALLOWED_TEST_KIND_DIRS))
        raise pytest.UsageError(
            "Test files must live under the kind-first top-level directories.\n"
            f"Allowed top-level kinds: {allowed}\n"
            f"Offending paths:\n{joined}"
        )
