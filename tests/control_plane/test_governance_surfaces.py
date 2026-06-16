"""Governance regression tests for control-plane metadata surfaces."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EXPLICIT_REFERENCE_SKILLS = {
    "clarify-and-goal",
    "code-intelligence",
    "promptfoo-evals",
}
BIDI_CONTROL_CHARS = {
    "\u202a",
    "\u202b",
    "\u202c",
    "\u202d",
    "\u202e",
    "\u2066",
    "\u2067",
    "\u2068",
    "\u2069",
}


def iter_skill_reference_files() -> list[Path]:
    """Return all skill reference markdown files under `.agents/skills`."""
    return sorted((REPO_ROOT / ".agents" / "skills").glob("*/references/*.md"))


def test_skills_do_not_use_generic_reference_readme_names() -> None:
    """Ensure repo-local skill references use purpose-specific filenames."""
    readme_refs = list((REPO_ROOT / ".agents" / "skills").glob("*/references/README.md"))

    assert readme_refs == []


def test_skill_reference_files_are_linked_from_skill_entrypoints() -> None:
    """Ensure explicit reference files are linked from their `SKILL.md` entrypoints."""
    for reference_path in iter_skill_reference_files():
        skill_dir = reference_path.parents[1]
        if skill_dir.name not in EXPLICIT_REFERENCE_SKILLS:
            continue
        skill_md = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        assert reference_path.name in skill_md


def test_adr_index_matches_committed_adr_files() -> None:
    """Ensure the ADR index stays aligned with committed ADR files."""
    adr_dir = REPO_ROOT / "docs" / "adr"
    committed_adrs = sorted(path.name for path in adr_dir.glob("[0-9][0-9][0-9][0-9]-*.md"))
    index_text = (adr_dir / "index.md").read_text(encoding="utf-8")
    indexed_adrs = sorted(re.findall(r"\[[^\]]+\]\((\d{4}-[^)]+\.md)\)", index_text))

    assert indexed_adrs == committed_adrs


def test_governance_surfaces_reject_bidi_control_characters() -> None:
    """Ensure critical governance surfaces do not contain bidi control characters."""
    targets = [
        REPO_ROOT / "AGENTS.md",
        REPO_ROOT / "README.md",
        REPO_ROOT / "CHANGELOG.md",
        REPO_ROOT / "pyproject.toml",
        REPO_ROOT / "package.json",
        REPO_ROOT / ".codex",
        REPO_ROOT / ".agents",
        REPO_ROOT / ".taskmaster",
        REPO_ROOT / ".specify",
        REPO_ROOT / "docs",
        REPO_ROOT / "policy",
    ]
    file_paths: list[Path] = []
    for target in targets:
        if target.is_file():
            file_paths.append(target)
            continue
        for path in target.rglob("*"):
            if path.is_file() and path.suffix in {
                ".md",
                ".toml",
                ".json",
                ".yaml",
                ".yml",
                ".rego",
                ".py",
                ".cjs",
            }:
                file_paths.append(path)

    offenders: list[str] = []
    for path in sorted(file_paths):
        text = path.read_text(encoding="utf-8")
        if any(char in text for char in BIDI_CONTROL_CHARS):
            offenders.append(path.relative_to(REPO_ROOT).as_posix())

    assert offenders == []
