# AGENTS.md

## Mission

Build **Library Ops** from the canonical PRD/spec pack and derived Task Master graph using Codex CLI, Spec Kit, Task Master, and the required local toolchain. This repository is a governed Codex control-plane package with explicit clarification, goal-setting, subagent escalation, and quality-gate policy.

## Source-of-truth order

1. `.specify/memory/constitution.md`
2. `.taskmaster/docs/prd.md`
3. `specs/001-core/*`
4. generated `.taskmaster/tasks/tasks.json` after PRD parsing
5. current Task Master task/subtask
6. this file, nested `AGENTS.md`, and `.codex/agents/*.toml`
7. relevant `.agents/skills/*/SKILL.md`
8. consolidated ADRs and supporting docs under `docs/`
9. source code and tests once implemented

## Required session start

Root coordinator mode: the interactive root agent must behave as the coordinator
by default. Do not rely on a Codex `default-agent` config key. Spawn the
`coordinator` subagent only for bounded synthesis; otherwise the root agent owns
source-of-truth order, routing, decisions, and final judgment.

1. Read the current task and linked PRD/spec section. If
   `.taskmaster/tasks/tasks.json` or a current task does not yet exist, read the
   constitution, canonical PRD, and `specs/001-core/*` first, then generate and
   validate the Task Master graph after coordinator/subagent setup is verified.
2. Check `git status`.
3. Confirm whether the change is meta/control-plane, product-code, or both; split commits accordingly.
4. Perform skill discovery before broad work: check the repo-local and installed skill catalog, load the relevant skill(s), and prefer explicit skill workflows over ad hoc repeated prompting. Use `clarify-and-goal` when ambiguity exists.
5. Use `/plan` and the native user-question path when available before high-risk implementation: `request_user_input` in Plan mode, `ask_user_question` if exposed by the active build, or MCP elicitation through `tool_call_mcp_elicitation`. Otherwise emit a Question packet.
6. Use `/goal` for long work after the goal is measurable and evidence-backed. For long-horizon work, omit a token budget by default; set one only when a hard stop, cost ceiling, or deliberate summarize-and-handoff checkpoint is actually needed.
7. Use Serena, code-review-graph, and ast-grep before broad source changes.
8. Use RTK for noisy exploratory commands and raw output for exact evidence.
9. Record decisions, evidence, and validation in Task Master notes.
10. Task Master mutations normally route through `taskmaster_governor`; root
    may read Task Master directly and may write only with an explicit note
    explaining why the governor path was not used.
11. Root plus direct specialists is the default orchestration posture unless an
    ADR and validator explicitly re-enable deeper recursion.

Do not rely on per-agent `skills.config` overrides as if they make a skill
always loaded for one subagent. Treat skill selection as a discovery and
routing problem owned by the root/coordinator, with explicit skill invocation
or clear trigger text as the reliable path.

Skill discovery flow:
1. Start with the repo-local catalog under `.agents/skills/`.
2. Use each skill's `name`, `description`, and `agents/openai.yaml` metadata as the first routing layer.
3. Prefer the strongest matching workflow skill or skill combination before ad hoc prompting.
4. If a workflow depends on an installed curated skill, route to it explicitly rather than assuming a subagent-local override will make it always loaded.

## Question packet

Use this shape when user input may alter scope, credentials, cost, security, architecture, MCPs, context budgets, remote branch/review policy, deployment, or irreversible repository state:

```text
Question packet
Decision needed:
Why this blocks or changes risk:
Options:
  A. <option> — tradeoff
  B. <option> — tradeoff
Recommended default:
Confidence:
Can proceed without answer? yes/no
Safe partial work while waiting:
Files/tasks affected:
Validation after answer:
```

## Escalation packet

Every subagent must return this packet when blocked, partial, needs-user, low-confidence, or risk-significant:

```text
Escalation packet
Status: clear | needs-user | blocked | partial
Confidence: 0.00-1.00
Finding:
Evidence:
Risk if ignored:
User question needed:
Recommended default:
Partial work safe to continue:
Owner agent:
Next validation:
```

The coordinator decides whether to ask the user, continue safe partial work, or stop.

If remote repository policy blocks a required merge, push, or release step, do
not work around it by switching to an alternate base branch, bypassing policy,
or assuming the action can happen later. Return `Status: blocked` with the exact
GitHub evidence and stop until the user changes the policy or gives an explicit
new instruction.

## Required selected stack

Implementation environments must provide Codex CLI, Task Master, RTK, Serena, code-review-graph, ast-grep, Repomix, Context7 MCP, Exa MCP, Task Master MCP, Promptfoo, Playwright, Schemathesis, mutmut, Vale, cspell, lychee, alex, agent-skills-lint, Gitleaks, Semgrep, Bandit, pip-audit, actionlint, zizmor, Conftest, CycloneDX, Import Linter, Ruff, Pyright, pytest, and Hypothesis.

Run:

```bash
codex doctor --summary --ascii --no-color
npx --yes --package task-master-ai@0.43.1 -c 'task-master validate-dependencies'
```

## Decision rules

Use `docs/decisioning/socratic-decision-framework.md` and `.codex/references/clarification-and-goals.md` for material choices. Do not pause merely because a required local tool needs to be configured or smoke-tested. Do pause before adding vendors, exporting source to cloud tools, changing project scope, or performing irreversible git/GitHub actions.

## Architecture rules

Use the hybrid architecture approach in `docs/architecture/architecture-approach.md`: Spec Kit as delivery/spec backbone, Task Master as derived graph, arc42 for quality/risk framing, C4 only where diagrams clarify, strategic DDD-lite only, and idiomatic Django layers.

## Required local gates

```bash
npm run skills:lint
npm run skills:audit
npm run docs:quality
npm run docstrings:coverage
npm run docstrings:lint
npm run eval:validate
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest
uv run python manage.py check
PYTHONPATH=src uv run lint-imports
npx --yes --package task-master-ai@0.43.1 -c 'task-master validate-dependencies'
```

Security/workflow/supply-chain:

```bash
gitleaks detect --source . --redact
uvx --from semgrep semgrep scan --config .semgrep.yml
uv run bandit -c pyproject.toml -r src
uv run pip-audit --progress-spinner off
npm audit --audit-level=moderate
actionlint
zizmor .
conftest test .codex/config.toml --policy policy
uv run cyclonedx-py environment --output-format json --output-file reports/sbom/python.cdx.json
```

## Repository hygiene

Never commit secrets, private MCP state, generated corpora, media, embeddings, local databases, code graph caches, Repomix output, Promptfoo result exports, virtualenvs, node_modules, or scan artifacts unless explicitly sanitized and approved.
