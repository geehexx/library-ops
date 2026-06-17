"""Governance regression tests for control-plane metadata surfaces."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EXPLICIT_REFERENCE_SKILLS = {
    "clarify-and-goal",
    "code-intelligence",
    "promptfoo-evals",
}
DELETED_ANCHOR_PATHS = {
    "PACKAGE_MANIFEST.md",
    ".codex/references/clarification-and-goals.md",
    ".codex/references/context-and-tooling-strategy.md",
    ".codex/references/context-lineage.md",
    ".agents/skills/clarify-and-goal/references/workflow-sources.md",
    ".agents/skills/code-intelligence/references/tool-routing.md",
}
RETIRED_DOC_SURFACES = {
    "docs/agent-system/",
    "docs/how-to/",
    "docs/setup/",
}
APP_LOCAL_TEMPLATE_FILES = {
    "src/libraryops/shell/templates/base.html",
    "src/libraryops/shell/templates/403.html",
    "src/libraryops/catalog/templates/catalog/create.html",
    "src/libraryops/catalog/templates/catalog/detail.html",
    "src/libraryops/catalog/templates/catalog/index.html",
    "src/libraryops/shell/templates/shell/home.html",
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


def test_coordinator_and_django_skill_encode_direct_specialists_and_pyright_first() -> None:
    """Ensure the coordinator and Django skill keep the routing and typing posture explicit."""
    coordinator_text = (REPO_ROOT / ".codex" / "agents" / "coordinator.toml").read_text(
        encoding="utf-8",
    )
    implementer_text = (REPO_ROOT / ".codex" / "agents" / "implementer.toml").read_text(
        encoding="utf-8",
    )
    django_skill_text = (
        REPO_ROOT / ".agents" / "skills" / "django-feature" / "SKILL.md"
    ).read_text(encoding="utf-8")
    django_prompt_text = (
        REPO_ROOT / ".agents" / "skills" / "django-feature" / "agents" / "openai.yaml"
    ).read_text(encoding="utf-8")

    assert "Spawn direct specialists only" in coordinator_text
    assert "default coordinator" in coordinator_text
    assert ".codex-session-notes/continuation.md" in coordinator_text
    assert "Pyright" in implementer_text
    assert "Pyright" in django_skill_text
    assert "Pyright" in django_prompt_text


def test_django_workaround_patterns_do_not_return() -> None:
    """Ensure direct field generics and explicit view redirects stay canonical."""
    model_paths = [
        REPO_ROOT / "src" / "libraryops" / "catalog" / "models.py",
        REPO_ROOT / "src" / "libraryops" / "inventory" / "models.py",
        REPO_ROOT / "src" / "libraryops" / "circulation" / "models.py",
        REPO_ROOT / "src" / "libraryops" / "audit" / "models.py",
    ]
    catalog_views_text = (REPO_ROOT / "src" / "libraryops" / "catalog" / "views.py").read_text(
        encoding="utf-8"
    )
    django_skill_text = (
        REPO_ROOT / ".agents" / "skills" / "django-feature" / "SKILL.md"
    ).read_text(encoding="utf-8")
    implementer_text = (REPO_ROOT / ".codex" / "agents" / "implementer.toml").read_text(
        encoding="utf-8"
    )

    for path in model_paths:
        text = path.read_text(encoding="utf-8")
        assert 'cast("models.DateTimeField' not in text
        assert "DateTimeField[" in text
    assert "HttpResponseRedirect(self.get_success_url())" in catalog_views_text
    assert "reportUnknownMemberType" not in catalog_views_text
    assert "Prefer direct `models.DateTimeField" in django_skill_text
    assert "Prefer explicit CBV redirects" in django_skill_text
    assert "Prefer direct `models.DateTimeField" in implementer_text
    assert "explicit CBV redirects" in implementer_text


def test_root_agents_and_references_encode_repo_local_handoff_and_astgrep_path() -> None:
    """Ensure canonical handoff and repo-local ast-grep paths stay explicit."""
    root_agents = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    clarify_skill = (REPO_ROOT / ".agents" / "skills" / "clarify-and-goal" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    code_intel_skill = (
        REPO_ROOT / ".agents" / "skills" / "code-intelligence" / "SKILL.md"
    ).read_text(encoding="utf-8")

    assert ".codex-session-notes/continuation.md" in root_agents
    assert "npm run astgrep:scan" in root_agents
    assert "Question packet" in clarify_skill
    assert "Escalation packet" in clarify_skill
    assert "code-review-graph" in code_intel_skill
    assert "ast-grep" in code_intel_skill


def test_retired_anchor_files_are_removed() -> None:
    """Ensure retired anchor files stay deleted."""
    for relative_path in DELETED_ANCHOR_PATHS:
        assert not (REPO_ROOT / relative_path).exists()
    assert not any((REPO_ROOT / ".codex" / "references").glob("**/*"))
    hook_text = (REPO_ROOT / ".codex" / "hooks" / "session_start_notice.py").read_text(
        encoding="utf-8"
    )
    for retired_path in DELETED_ANCHOR_PATHS:
        assert retired_path not in hook_text


def test_hub_indexes_stay_on_canonical_surface_paths() -> None:
    """Ensure hub surfaces point at canonical entry points and avoid retired paths."""
    llms_text = (REPO_ROOT / "llms.txt").read_text(encoding="utf-8")
    workflow_sources_text = (
        REPO_ROOT / ".agents" / "skills" / "clarify-and-goal" / "SKILL.md"
    ).read_text(encoding="utf-8")
    code_intel_text = (
        REPO_ROOT / ".agents" / "skills" / "code-intelligence" / "SKILL.md"
    ).read_text(encoding="utf-8")

    required_llms = [
        "AGENTS.md",
        ".codex/agents/",
        ".agents/skills/",
        ".taskmaster/docs/prd.md",
        "specs/001-core/",
        "README.md",
    ]
    required_clarify = [
        "AGENTS.md",
        ".taskmaster/docs/prd.md",
        "Question packet",
        "Escalation packet",
        "docs/process/quality-gates.md",
    ]
    required_code_intel = [
        "AGENTS.md",
        ".taskmaster/docs/prd.md",
        "code-review-graph",
        "ast-grep",
        "docs/process/quality-gates.md",
    ]

    for needle in required_llms:
        assert needle in llms_text
    for needle in required_clarify:
        assert needle in workflow_sources_text
    for needle in required_code_intel:
        assert needle in code_intel_text

    for retired_surface in RETIRED_DOC_SURFACES:
        assert retired_surface not in llms_text
        assert retired_surface not in workflow_sources_text
        assert retired_surface not in code_intel_text

    assert ".taskmaster/README.md" not in workflow_sources_text
    assert ".taskmaster/README.md" not in code_intel_text
    assert "docs/agent-system/" not in llms_text
    assert "docs/agent-system/" not in workflow_sources_text
    assert "docs/agent-system/" not in code_intel_text


def test_templates_surface_stays_shared_only_at_repo_root() -> None:
    """Ensure app-owned HTML templates stay in app-local template directories."""
    template_root = REPO_ROOT / "templates"
    root_html_files = sorted(
        path.relative_to(template_root).as_posix() for path in template_root.rglob("*.html")
    )

    assert root_html_files == []
    for relative_path in APP_LOCAL_TEMPLATE_FILES:
        assert (REPO_ROOT / relative_path).exists()


def test_adr_index_matches_committed_adr_files() -> None:
    """Ensure the ADR index stays aligned with committed ADR files."""
    adr_dir = REPO_ROOT / "docs" / "adr"
    committed_adrs = sorted(path.name for path in adr_dir.glob("[0-9][0-9][0-9][0-9]-*.md"))
    index_text = (adr_dir / "index.md").read_text(encoding="utf-8")
    indexed_adrs = sorted(re.findall(r"\[[^\]]+\]\((\d{4}-[^)]+\.md)\)", index_text))

    assert indexed_adrs == committed_adrs


def test_docs_inclusive_and_repomix_cover_hub_indexes() -> None:
    """Ensure inclusive docs and repomix include the hub/index surfaces."""
    package_json = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))
    repomix_config = json.loads((REPO_ROOT / "repomix.config.json").read_text(encoding="utf-8"))

    docs_inclusive = package_json["scripts"]["docs:inclusive"]
    include_entries = repomix_config["include"]

    assert ".codex/agents" in docs_inclusive
    assert "llms.txt" in docs_inclusive
    assert ".codex/agents/**/*.toml" in include_entries
    assert "llms.txt" in include_entries
    assert "PACKAGE_MANIFEST.md" not in docs_inclusive
    assert "PACKAGE_MANIFEST.md" not in include_entries
    assert ".codex/references" not in docs_inclusive
    assert ".codex/references/**/*.md" not in include_entries
    for retired_surface in RETIRED_DOC_SURFACES:
        assert retired_surface not in docs_inclusive
        assert retired_surface not in include_entries


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


def test_product_tests_live_under_tests_tree_only() -> None:
    """Ensure product tests do not reappear under the application package tree."""

    offenders = sorted(
        {
            *(
                path.relative_to(REPO_ROOT).as_posix()
                for path in (REPO_ROOT / "src" / "libraryops").rglob("test_*.py")
            ),
            *(
                path.relative_to(REPO_ROOT).as_posix()
                for path in (REPO_ROOT / "src" / "libraryops").rglob("*_test.py")
            ),
        }
    )

    assert offenders == []


def test_product_python_modules_do_not_depend_on_type_checking_shims() -> None:
    """Ensure the product slice does not reintroduce `TYPE_CHECKING`-only shims."""

    product_paths = [
        REPO_ROOT / "src" / "libraryops" / "accounts",
        REPO_ROOT / "src" / "libraryops" / "audit",
        REPO_ROOT / "src" / "libraryops" / "catalog",
        REPO_ROOT / "src" / "libraryops" / "circulation",
        REPO_ROOT / "src" / "libraryops" / "inventory",
        REPO_ROOT / "src" / "libraryops" / "web",
    ]
    offenders: list[str] = []
    for root in product_paths:
        for path in root.rglob("*.py"):
            if "TYPE_CHECKING" in path.read_text(encoding="utf-8"):
                offenders.append(path.relative_to(REPO_ROOT).as_posix())

    assert offenders == []
