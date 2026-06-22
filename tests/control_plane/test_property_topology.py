"""Govern the placement and marker contract for property-based tests."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_ROOT = REPO_ROOT / "tests"
PROPERTY_ROOT = TEST_ROOT / "property"


def _qualified_name(node: ast.expr) -> str:
    """Return a dotted name for a simple name/attribute expression."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _qualified_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _imports_hypothesis(tree: ast.Module) -> bool:
    """Return whether a module imports Hypothesis directly or by submodule."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(
                alias.name == "hypothesis" or alias.name.startswith("hypothesis.")
                for alias in node.names
            ):
                return True
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "hypothesis" or module.startswith("hypothesis."):
                return True
    return False


def _has_module_property_marker(tree: ast.Module) -> bool:
    """Return whether the module declares ``pytestmark = pytest.mark.property``."""
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        value = node.value
        if value is None:
            continue
        has_pytestmark_target = any(
            isinstance(target, ast.Name) and target.id == "pytestmark" for target in targets
        )
        if has_pytestmark_target and _qualified_name(value) == "pytest.mark.property":
            return True
    return False


def _has_property_decorator(tree: ast.Module) -> bool:
    """Return whether any function/class uses ``pytest.mark.property`` directly."""
    for node in ast.walk(tree):
        decorators = getattr(node, "decorator_list", ())
        if any(_qualified_name(decorator) == "pytest.mark.property" for decorator in decorators):
            return True
    return False


def _test_modules() -> list[Path]:
    """Return all Python test modules in deterministic order."""
    return sorted(TEST_ROOT.rglob("test_*.py"))


def test_hypothesis_tests_live_only_under_the_property_bucket() -> None:
    """Keep generated tests out of unit/integration/e2e topology buckets."""
    offenders: list[str] = []
    for path in _test_modules():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if _imports_hypothesis(tree) and not path.is_relative_to(PROPERTY_ROOT):
            offenders.append(path.relative_to(REPO_ROOT).as_posix())

    assert offenders == [], "Hypothesis tests belong under tests/property:\n" + "\n".join(offenders)


def test_property_marker_is_not_applied_outside_the_property_bucket() -> None:
    """Prevent marker-only property tests from bypassing the import check."""
    offenders: list[str] = []
    for path in _test_modules():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        has_property_marker = _has_property_decorator(tree) or _has_module_property_marker(tree)
        if has_property_marker and not path.is_relative_to(PROPERTY_ROOT):
            offenders.append(path.relative_to(REPO_ROOT).as_posix())

    assert offenders == [], "Property markers belong under tests/property:\n" + "\n".join(offenders)


def test_every_property_module_has_one_module_level_marker() -> None:
    """Make ``pytest -m property`` complete without per-test marker drift."""
    offenders: list[str] = []
    for path in sorted(PROPERTY_ROOT.rglob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if not _has_module_property_marker(tree):
            offenders.append(path.relative_to(REPO_ROOT).as_posix())

    assert offenders == [], "Add `pytestmark = pytest.mark.property` to:\n" + "\n".join(offenders)
