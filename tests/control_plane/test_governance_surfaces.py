"""Governance regression tests for control-plane metadata surfaces."""

from __future__ import annotations

import ast
import json
import re
import tomllib
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
    "src/libraryops/accounts/templates/account/login.html",
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
LOCAL_ONLY_GOVERNANCE_FILES = {
    ".taskmaster/state.json",
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
    config = tomllib.loads((REPO_ROOT / ".codex" / "config.toml").read_text(encoding="utf-8"))
    config_text = (REPO_ROOT / ".codex" / "config.toml").read_text(encoding="utf-8")
    commitlint_text = (REPO_ROOT / "commitlint.config.cjs").read_text(encoding="utf-8")
    implementer_text = (REPO_ROOT / ".codex" / "agents" / "implementer.toml").read_text(
        encoding="utf-8",
    )
    debugger_text = (REPO_ROOT / ".codex" / "agents" / "debugger.toml").read_text(
        encoding="utf-8",
    )
    single_file_text = (REPO_ROOT / ".codex" / "agents" / "single-file-implementer.toml").read_text(
        encoding="utf-8"
    )
    django_skill_text = (
        REPO_ROOT / ".agents" / "skills" / "django-feature" / "SKILL.md"
    ).read_text(encoding="utf-8")
    django_prompt_text = (
        REPO_ROOT / ".agents" / "skills" / "django-feature" / "agents" / "openai.yaml"
    ).read_text(encoding="utf-8")

    assert config["permissions"]["coordinator_root"]["extends"] == ":workspace"
    assert "model_context_window = 500000" in config_text
    assert "max_threads = 24" in config_text
    commitlint_scope_match = re.search(
        r"(?ms)^\s*'scope-enum': \[\s*2,\s*'always',\s*(\[[^\]]+\])\s*\]",
        commitlint_text,
    )
    assert commitlint_scope_match is not None
    commitlint_scopes = ast.literal_eval(commitlint_scope_match.group(1))
    assert "render" in commitlint_scopes
    assert "command_runner" in coordinator_text
    assert "context_gatherer" in coordinator_text
    assert "implementer" in coordinator_text
    assert "debugger" in coordinator_text
    assert "single_file_implementer" in coordinator_text
    assert "Pyright" in implementer_text
    assert 'model = "gpt-5.3-codex-spark"' in debugger_text
    assert 'sandbox_mode = "danger-full-access"' in debugger_text
    assert 'model = "gpt-5.3-codex-spark"' in single_file_text
    assert 'sandbox_mode = "danger-full-access"' in single_file_text
    assert "Pyright" in django_skill_text
    assert "Pyright" in django_prompt_text
    assert (
        "Use manager/model methods first for aggregate-specific CRUD/archive" in django_skill_text
    )
    assert "manager/model methods first for aggregate-specific CRUD/archive behavior" in (
        implementer_text
    )
    assert "service/selector/model layering" not in implementer_text


def test_routing_skills_name_the_spark_lanes_and_direct_entrypoints() -> None:
    """Ensure the routing skills name the Spark lanes and direct entrypoints."""
    coordinator_text = (REPO_ROOT / ".codex" / "agents" / "coordinator.toml").read_text(
        encoding="utf-8"
    )
    root_agents_text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    code_intelligence_text = (
        REPO_ROOT / ".agents" / "skills" / "code-intelligence" / "SKILL.md"
    ).read_text(encoding="utf-8")
    clarify_goal_text = (
        REPO_ROOT / ".agents" / "skills" / "clarify-and-goal" / "SKILL.md"
    ).read_text(encoding="utf-8")

    for text in (coordinator_text, root_agents_text, code_intelligence_text, clarify_goal_text):
        for expected_fragment in ("command_runner", "context_gatherer", "implementer"):
            assert expected_fragment in text

    assert "root-local shell/file exploration available" in clarify_goal_text


def test_codex_config_and_rules_preserve_default_approved_mcp_and_hook_policy() -> None:
    """Ensure the coordinator-default config and hook rules do not silently drift."""
    config = tomllib.loads((REPO_ROOT / ".codex" / "config.toml").read_text(encoding="utf-8"))
    agents = config["agents"]
    package_json = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))
    scripts = package_json["scripts"]
    coordinator_text = (REPO_ROOT / ".codex" / "agents" / "coordinator.toml").read_text(
        encoding="utf-8"
    )
    runtime_policy_text = (REPO_ROOT / ".taskmaster" / "docs" / "runtime-policy.md").read_text(
        encoding="utf-8"
    )
    command_runner_text = (REPO_ROOT / ".codex" / "agents" / "command-runner.toml").read_text(
        encoding="utf-8"
    )
    code_intelligence_text = (
        REPO_ROOT / ".agents" / "skills" / "code-intelligence" / "SKILL.md"
    ).read_text(encoding="utf-8")
    context_gatherer_text = (REPO_ROOT / ".codex" / "agents" / "context-gatherer.toml").read_text(
        encoding="utf-8"
    )
    coordinator_launcher_text = (REPO_ROOT / "scripts" / "codex-coordinator.sh").read_text(
        encoding="utf-8"
    )
    runtime_env_script = (REPO_ROOT / "scripts" / "codex-runtime-env.sh").read_text(
        encoding="utf-8"
    )
    quality_gates_text = (REPO_ROOT / "docs" / "process" / "quality-gates.md").read_text(
        encoding="utf-8"
    )
    policy_text = (REPO_ROOT / "policy" / "codex.rego").read_text(encoding="utf-8")

    assert config["model_context_window"] == 500000
    assert agents["max_threads"] == 24
    assert agents["max_depth"] == 2
    assert "debugger" in agents
    assert "single_file_implementer" in agents

    workspace_roots = config["permissions"]["workspace"]["workspace_roots"]
    assert workspace_roots["~/.render"] is True

    mcp_servers = config["mcp_servers"]
    for server_name in ("context7", "exa", "taskmaster-ai", "code-review-graph", "serena"):
        server = mcp_servers[server_name]
        assert server["required"] is True
        assert server["default_tools_approval_mode"] == "approve"

    rules_text = (REPO_ROOT / ".codex" / "rules" / "default.rules").read_text(encoding="utf-8")
    hook_rule_match = re.search(
        r'(?ms)^prefix_rule\(\n\s+pattern = \["uv", "run", "--no-sync", "--project"\],.*?^\)\n',
        rules_text,
    )

    assert hook_rule_match is not None
    hook_rule_text = hook_rule_match.group(0)
    for expected_fragment in (
        ".codex/hooks/session_start_notice.py",
        '.codex/hooks/serena_hook.py\\" activate',
        '.codex/hooks/serena_hook.py\\" cleanup',
        ".codex/hooks/session_stop_notice.py",
    ):
        assert expected_fragment in hook_rule_text

    for expected_fragment in (
        "command_runner",
        "context_gatherer",
        "implementer",
        "debugger",
        "single_file_implementer",
        "docs_researcher",
    ):
        assert expected_fragment in coordinator_text

    for expected_fragment in (
        "scripts/codex-runtime-env.sh",
        'codex --cd "$ROOT_DIR" --strict-config',
    ):
        assert expected_fragment in coordinator_launcher_text

    assert "Context7 first" in quality_gates_text
    for script_name in ("markdownlint", "python:lint", "python:complexity", "skills:audit"):
        assert "scripts/codex-runtime-env.sh" in scripts[script_name]
    assert ".codex/.tmp" in scripts["markdownlint"]
    assert ".codex/skills" in scripts["markdownlint"]
    assert "lint.mccabe.max-complexity = 6" in scripts["python:complexity"]
    assert "npm run python:complexity" in scripts["python:lint"]
    assert ".agents/skills" in scripts["docs:style"]
    assert ".codex/.tmp" in scripts["docs:style"]
    assert ".codex/skills" in scripts["docs:style"]
    assert ".agents/skills/**" in scripts["docs:spell"]
    assert ".codex/.tmp/**" in scripts["docs:spell"]
    assert ".codex/skills/**" in scripts["docs:spell"]
    assert "tests/**" in scripts["docs:spell"]

    for expected_fragment in (
        "scripts/codex-runtime-env.sh",
        "npm_config_cache",
        "Do not read `.taskmaster/state.json` directly",
    ):
        assert expected_fragment in runtime_policy_text

    assert "Cache-safe command wrapper for npm and gh" in rules_text

    for expected_fragment in (
        "SCRIPT_DIR",
        "REPO_ROOT",
        "prepare_runtime_cache_root",
        "choose_runtime_cache_root",
        'preferred_root="${TMPDIR:-/tmp}/library-ops-codex"',
        'fallback_root="$REPO_ROOT/.codex/.tmp/library-ops-codex"',
        'RUNTIME_CACHE_ROOT="$(choose_runtime_cache_root)"',
        "npm_config_cache",
        "XDG_CACHE_HOME",
        "PROMPTFOO_CACHE_PATH",
        "PROMPTFOO_CONFIG_DIR",
        "PROMPTFOO_LOG_DIR",
        "PIP_CACHE_DIR",
        "PLAYWRIGHT_BROWSERS_PATH",
        "UV_CACHE_DIR",
        "usage: bash scripts/codex-runtime-env.sh",
    ):
        assert expected_fragment in runtime_env_script

    assert "command_runner" in coordinator_text
    assert "context_gatherer" in coordinator_text
    assert "implementer" in coordinator_text
    assert "Spark-first handling" in code_intelligence_text

    assert "model_reasoning_summary" not in command_runner_text
    assert 'model = "gpt-5.3-codex-spark"' in command_runner_text
    assert 'model = "gpt-5.3-codex-spark"' in context_gatherer_text
    assert "Spark repo and source-map collector for local evidence." in context_gatherer_text
    assert "bounded child worker" in context_gatherer_text
    assert 'sandbox_mode = "danger-full-access"' in context_gatherer_text

    speckit_text = (REPO_ROOT / ".codex" / "agents" / "speckit-governor.toml").read_text(
        encoding="utf-8"
    )
    assert "Batch reasoning before tools" in speckit_text

    for expected_fragment in (
        "default_tools_approval_mode",
        "MCP server must default to approve",
    ):
        assert expected_fragment in policy_text


def test_django_workaround_patterns_do_not_return() -> None:
    """Ensure direct field generics and explicit view redirects stay canonical."""
    model_paths = [
        REPO_ROOT / "src" / "libraryops" / "catalog" / "models.py",
        REPO_ROOT / "src" / "libraryops" / "inventory" / "models.py",
        REPO_ROOT / "src" / "libraryops" / "circulation" / "models.py",
        REPO_ROOT / "src" / "libraryops" / "audit" / "models.py",
    ]
    catalog_views_text = (
        REPO_ROOT / "src" / "libraryops" / "catalog" / "views" / "base.py"
    ).read_text(encoding="utf-8")
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
    assert (
        "Use manager/model methods first for aggregate-specific CRUD/archive" in django_skill_text
    )
    assert "manager/model methods first for aggregate-specific CRUD/archive behavior" in (
        implementer_text
    )


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


def test_skill_discovery_stays_on_direct_skill_files_and_not_serena_memory_reads() -> None:
    """Ensure skill discovery and goal routing stay on direct skill files."""
    root_agents = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    clarify_skill = (REPO_ROOT / ".agents" / "skills" / "clarify-and-goal" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    code_intel_skill = (
        REPO_ROOT / ".agents" / "skills" / "code-intelligence" / "SKILL.md"
    ).read_text(encoding="utf-8")
    coordinator_text = (REPO_ROOT / ".codex" / "agents" / "coordinator.toml").read_text(
        encoding="utf-8"
    )
    architect_text = (
        REPO_ROOT / ".codex" / "agents" / "code-intelligence-architect.toml"
    ).read_text(encoding="utf-8")

    for expected_fragment in (
        "read the relevant `SKILL.md` entrypoint directly",
        "Do not use Serena memory reads",
    ):
        assert expected_fragment in root_agents

    for expected_fragment in (
        "Read the matching `SKILL.md` entrypoint from `.agents/skills/` directly.",
        "Do not use Serena memory reads or other proxy lookups",
    ):
        assert expected_fragment in clarify_skill

    for expected_fragment in (
        "relevant `SKILL.md` directly to select the skill",
        "Serena only comes after",
    ):
        assert expected_fragment in code_intel_skill

    for expected_fragment in (
        "relevant `SKILL.md` directly from `.agents/skills/` to choose the",
        "Serena is for symbol-aware code context after selection",
    ):
        assert expected_fragment in coordinator_text

    for expected_fragment in (
        "Select the skill from the actual `SKILL.md` entrypoint under `.agents/skills/`",
        "symbol-aware code context after the skill",
        "not for discovery",
    ):
        assert expected_fragment in architect_text


def test_review_taskmaster_and_prd_skills_make_test_rigor_explicit() -> None:
    """Ensure review and planning skills surface Spark-first review flow and evidence."""
    review_text = (REPO_ROOT / ".agents" / "skills" / "review" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    define_goal_text = (REPO_ROOT / ".agents" / "skills" / "define-goal" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    taskmaster_text = (REPO_ROOT / ".agents" / "skills" / "taskmaster" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    prd_text = (REPO_ROOT / ".agents" / "skills" / "prd-architect" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    clarify_text = (REPO_ROOT / ".agents" / "skills" / "clarify-and-goal" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    taskmaster_prompt_text = (
        REPO_ROOT / ".agents" / "skills" / "taskmaster" / "agents" / "openai.yaml"
    ).read_text(encoding="utf-8")
    define_goal_prompt_text = (
        REPO_ROOT / ".agents" / "skills" / "define-goal" / "agents" / "openai.yaml"
    ).read_text(encoding="utf-8")
    clarify_goal_prompt_text = (
        REPO_ROOT / ".agents" / "skills" / "clarify-and-goal" / "agents" / "openai.yaml"
    ).read_text(encoding="utf-8")

    assert "bounded or single-file reviews" in review_text
    assert "Spark lanes first" in review_text
    assert "Acceptance criteria and pass/fail evidence" in review_text
    assert "Acceptance criteria:" in review_text
    assert "Pass/fail evidence:" in review_text

    assert "acceptance criteria, test quality, and pass/fail evidence" in taskmaster_text
    assert "route through `$clarify-and-goal` before expanding" in taskmaster_text
    assert "acceptance-criteria status" in taskmaster_text
    assert "pass/fail evidence recorded" in taskmaster_text
    assert "Acceptance criteria:" in taskmaster_text
    assert "Pass/fail evidence:" in taskmaster_text
    assert "Keep the goal broad and stable" in define_goal_text
    assert "Task Master for implementation detail" in define_goal_text
    assert "Broad goals stay broad and measurable" in define_goal_text
    assert "Task Master tasks, subtasks, or notes before coding" in define_goal_text
    assert (
        "keep concrete implementation detail in Task Master tasks, subtasks, or notes before coding"
        in taskmaster_prompt_text
    )
    assert (
        "move implementation detail into Task Master tasks, subtasks, or notes"
        in define_goal_prompt_text
    )
    assert (
        "keep concrete implementation detail in Task Master tasks, subtasks, or notes before coding"
        in clarify_goal_prompt_text
    )

    assert "explicit acceptance criteria, pass/fail evidence" in prd_text
    assert "test-quality expectations are ambiguous" in prd_text

    assert "unclear acceptance criteria" in clarify_text
    assert "unclear acceptance criteria, pass/fail evidence, or test-quality" in clarify_text
    assert "expectations as decision-dependent" in clarify_text
    assert "pass/fail evidence" in clarify_text
    assert (
        "Task Master tasks, subtasks, and notes so the goal stays stable as new slices appear"
        in clarify_text
    )


def test_spark_policy_routes_command_and_exploration_work_to_micro_workers() -> None:
    """Ensure the Spark policy explicitly routes commands and exploration to micro-workers."""
    adr_text = (
        REPO_ROOT / "docs" / "adr" / "0008-two-level-agent-orchestration-and-spark-fanout.md"
    ).read_text(encoding="utf-8")
    index_text = (REPO_ROOT / "docs" / "adr" / "index.md").read_text(encoding="utf-8")
    coordinator_text = (REPO_ROOT / ".codex" / "agents" / "coordinator.toml").read_text(
        encoding="utf-8"
    )
    root_agents_text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")

    for expected_fragment in (
        "Hybrid Direct-Specialist Orchestration With Spark Micro-Workers",
        "command_runner",
        "context_gatherer",
        "researcher",
        "docs_researcher",
    ):
        assert expected_fragment in adr_text
    for expected_fragment in (
        "command_runner",
        "context_gatherer",
        "implementer",
        "researcher",
        "docs_researcher",
    ):
        assert expected_fragment in coordinator_text or expected_fragment in root_agents_text

    assert "Hybrid direct-specialist orchestration with Spark micro-workers." in index_text
    assert "Batch reasoning before tools" in coordinator_text
    assert "Batch reasoning before tools" in root_agents_text
    assert "bounded child-worker fan-out" in coordinator_text


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


def test_hooks_json_does_not_register_pre_tool_use_reminder() -> None:
    """Ensure the noisy PreToolUse Serena reminder is not wired back in."""
    hooks_path = REPO_ROOT / ".codex" / "hooks.json"
    hooks = json.loads(hooks_path.read_text(encoding="utf-8"))

    assert "PreToolUse" not in hooks["hooks"]


def test_stop_hook_stays_notice_only() -> None:
    """Ensure the stop hook keeps emitting notice-only JSON."""
    stop_hook_text = (REPO_ROOT / ".codex" / "hooks" / "session_stop_notice.py").read_text(
        encoding="utf-8"
    )

    for expected_fragment in (
        "build_notice",
        'return emit_json({"notice": build_notice(dirty_entries)})',
        "return emit_json({})",
    ):
        assert expected_fragment in stop_hook_text
    assert "raise SystemExit(1)" not in stop_hook_text


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
    assert "tests" not in docs_inclusive
    assert ".codex/**/*.toml" in include_entries
    assert ".codex/hooks/**/*.py" in include_entries
    assert "llms.txt" not in include_entries
    assert "PACKAGE_MANIFEST.md" not in docs_inclusive
    assert "PACKAGE_MANIFEST.md" not in include_entries
    assert ".codex/references" not in docs_inclusive
    assert ".codex/references/**/*.md" not in include_entries
    for retired_surface in RETIRED_DOC_SURFACES:
        assert retired_surface not in docs_inclusive
        assert retired_surface not in include_entries


def test_catalog_forms_and_views_are_package_reexports() -> None:
    """Ensure the catalog app exposes package-level re-exports for forms and views."""
    from libraryops.catalog import forms as catalog_forms
    from libraryops.catalog import views as catalog_views

    assert catalog_forms.__all__ == [
        "CatalogFoundationCreateForm",
        "CopyForm",
        "EditionForm",
        "WorkForm",
    ]
    assert catalog_views.__all__ == [
        "CatalogCreateView",
        "CatalogDetailView",
        "CatalogIndexView",
        "CopyArchiveView",
        "CopyCreateView",
        "CopyUpdateView",
        "EditionArchiveView",
        "EditionCreateView",
        "EditionUpdateView",
        "WorkArchiveView",
        "WorkCreateView",
        "WorkUpdateView",
    ]
    assert not (REPO_ROOT / "src" / "libraryops" / "catalog" / "forms.py").exists()
    assert not (REPO_ROOT / "src" / "libraryops" / "catalog" / "views.py").exists()


def test_promptfoo_lane_routes_runtime_state_into_tmpdir() -> None:
    """Ensure promptfoo scripts and docs keep config, logs, and WAL out of home."""
    package_json = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))
    eval_strategy_text = (REPO_ROOT / "docs" / "evaluation" / "eval-strategy.md").read_text(
        encoding="utf-8"
    )
    promptfoo_skill_text = (
        REPO_ROOT / ".agents" / "skills" / "promptfoo-evals" / "SKILL.md"
    ).read_text(encoding="utf-8")
    runtime_env_script = (REPO_ROOT / "scripts" / "codex-runtime-env.sh").read_text(
        encoding="utf-8"
    )
    runtime_policy_text = (REPO_ROOT / ".taskmaster" / "docs" / "runtime-policy.md").read_text(
        encoding="utf-8"
    )

    for script_name in ("eval:validate", "eval:smoke", "eval:provider:local"):
        assert "scripts/codex-runtime-env.sh" in package_json["scripts"][script_name]

    for expected_fragment in (
        "PROMPTFOO_CONFIG_DIR",
        "PROMPTFOO_LOG_DIR",
        "npm_config_cache",
        "XDG_CACHE_HOME",
    ):
        assert expected_fragment in runtime_env_script

    for expected_fragment in (
        "scripts/codex-runtime-env.sh",
        "PROMPTFOO_CONFIG_DIR",
        "PROMPTFOO_LOG_DIR",
        "promptfoo state/logs stay under `TMPDIR`",
    ):
        assert expected_fragment in eval_strategy_text

    for expected_fragment in (
        "scripts/codex-runtime-env.sh",
        "PROMPTFOO_LOG_DIR",
        "Use `scripts/codex-runtime-env.sh` before promptfoo commands",
    ):
        assert expected_fragment in promptfoo_skill_text

    for expected_fragment in (
        "PROMPTFOO_CONFIG_DIR",
        "PROMPTFOO_LOG_DIR",
        "~/.promptfoo",
    ):
        assert expected_fragment in runtime_policy_text


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
        relative_path = path.relative_to(REPO_ROOT).as_posix()
        if relative_path in LOCAL_ONLY_GOVERNANCE_FILES:
            continue
        text = path.read_text(encoding="utf-8")
        if any(char in text for char in BIDI_CONTROL_CHARS):
            offenders.append(relative_path)

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
    """Ensure the product slice does not reintroduce hidden typing import shims."""

    product_paths = [
        REPO_ROOT / "src" / "libraryops" / "accounts",
        REPO_ROOT / "src" / "libraryops" / "audit",
        REPO_ROOT / "src" / "libraryops" / "catalog",
        REPO_ROOT / "src" / "libraryops" / "circulation",
        REPO_ROOT / "src" / "libraryops" / "inventory",
        REPO_ROOT / "src" / "libraryops" / "web",
    ]

    def has_hidden_typing_shim(text: str) -> bool:
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return False

        for node in ast.walk(tree):
            if not isinstance(node, ast.If):
                continue

            guard = node.test
            is_type_checking_guard = (
                (isinstance(guard, ast.Name) and guard.id == "TYPE_CHECKING")
                or (
                    isinstance(guard, ast.Attribute)
                    and isinstance(guard.value, ast.Name)
                    and guard.value.id == "typing"
                    and guard.attr == "TYPE_CHECKING"
                )
                or (isinstance(guard, ast.Constant) and guard.value is False)
            )
            if not is_type_checking_guard:
                continue

            if any(isinstance(stmt, (ast.Import, ast.ImportFrom)) for stmt in node.body):
                return True

        return False

    offenders: list[str] = []
    for root in product_paths:
        for path in root.rglob("*.py"):
            if has_hidden_typing_shim(path.read_text(encoding="utf-8")):
                offenders.append(path.relative_to(REPO_ROOT).as_posix())

    assert offenders == []
