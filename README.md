# Library Ops

**Library Ops** is an interview-demo library management system plus the Codex
control plane used to build it safely. The repository is intentionally split
between product truth, agent-control truth, committed execution artifacts, and
transient local outputs so an evaluator can see both the planned application
and the quality system around it.

## Evaluator fast path

Start here if you are reviewing the project for the interview.

```bash
npm ci
uv sync --all-groups
npm run checks:precommit
npm run docs:quality
npm run verify:core
npm run eval:ci
npx --yes --package task-master-ai@0.43.1 -c 'task-master validate-dependencies'
```

The full local gate is:

```bash
npm run verify:all
```

The faster full local loop, excluding the full security aggregate, is:

```bash
npm run verify:core
```

The fastest local hygiene loop is:

```bash
npm run checks:precommit
```

For a fresh session that should use the repo-local coordinator-default flow,
launch Codex through `./scripts/codex-coordinator.sh`. See `SETUP.md` for the
canonical bootstrap and operator commands.

Continuation state lives locally in:

- `.codex-session-notes/continuation.md`
- `.codex-session-notes/scratch.md`

These files are gitignored on purpose. They replace `/tmp/prompt.md` as the
canonical handoff pattern for this repo.

Some gates require local tools, MCP auth, browser access, or provider approval.
When a gate cannot run in the current environment, record the exact blocker in
the current task notes and, if useful, a local `reports/validation/*` artifact
rather than claiming the check passed.

## What this repo contains

| Area | Where to look | Evaluator signal |
|---|---|---|
| Product contract | `.taskmaster/docs/prd.md`, `specs/001-core/` | Library domain, user journeys, acceptance criteria, task-generation source. |
| Agent control plane | `AGENTS.md`, `.codex/`, `.agents/skills/` | Coordinator rules, subagents, skills, hooks, MCP policy, escalation behavior. |
| Architecture and decisions | `docs/ARCHITECTURE.md`, `docs/adr/`, `docs/reference/` | arc42/C4/DDD-lite direction, decision records, and durable reference material. |
| Human documentation | `SETUP.md`, `docs/AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/README.md`, `docs/design/wireframes.md`, `docs/evaluation/eval-strategy.md`, `docs/reference/context-lineage.md`, `docs/reference/question-packet-schema.md`, `docs/process/quality-gates.md`, `docs/process/retrospective.md`, `docs/process/sdlc.md` | Canonical bootstrap, docs-local decisioning, architecture rationale, evaluator-facing design/evaluation guidance, stable reference material, session lessons, and validation/release flow. |
| Documentation policy | `docs/AGENTS.md` | Docs-local placement rules and maintenance boundaries. |
| Quality gates | `policy/`, `.github/`, `promptfooconfig.yaml`, `evals/`, direct npm/uv/npx commands | Workflow security, docs quality, Promptfoo evals, and direct-tool validation. |
| Transient local outputs | `reports/**` | Ignored local validation summaries, Promptfoo output, SBOMs, and other derived run artifacts. |

## Source-of-truth order

1. `.specify/memory/constitution.md`
2. `.taskmaster/docs/prd.md`
3. `specs/001-core/*`
4. generated `.taskmaster/tasks/tasks.json` after PRD parsing and validation
5. current Task Master task/subtask
6. `AGENTS.md`, nested `AGENTS.md`, and `.codex/agents/*.toml`
7. `.agents/skills/*/SKILL.md`
8. consolidated ADRs and supporting docs under `docs/`
9. source code and tests
10. this README as the evaluator map

If these conflict, stop and update the higher-priority artifact first. Task Master tasks are derived execution artifacts; they are not canonical product truth.

## Canonical, derived, and local artifacts

| Class | Examples | Rule |
|---|---|---|
| Canonical | Constitution, PRD, specs, `AGENTS.md`, `.codex/`, `.agents/skills/`, durable docs, CI/policy config | Commit deliberately and keep coherent. |
| Derived | `.taskmaster/tasks/tasks.json`, local Promptfoo results, Repomix packs, SBOMs, graph databases, validation transcripts | Regenerate, review, and commit only the derived artifacts the repo intentionally keeps. Most local outputs belong under ignored `reports/**` paths and should not be treated as primary truth. |
| Operator-local | `.env*`, `.mcp.json`, `.taskmaster/config.json`, `.taskmaster/state.json`, OAuth/session state, local DBs, caches, `node_modules`, `.venv` | Never commit or package. |

## Current release status

The release-evidence slice is not fully complete yet. The current Render
deployment probe is timing out, so the live service is still unverified on
this branch. The OpenAPI shell exists, and Render deployment is scaffolded on
this branch, but the live service has not yet been proven end-to-end for this
branch.

Evaluator-facing expectations:

- use the Render deployment path as the current review target;
- sign in with the documented demo accounts after seeding or on the seeded live
  environment;
- expect password-based demo auth to work first; OAuth/social auth remains
  optional and environment-driven;
- expect OpenAPI to exist as a shell, not as final release evidence yet.

Known limitations:

- live deployment proof is still pending for this branch;
- migrations, static assets, and health checks have not yet been verified on the
  live service here;
- release tagging, demo script, and full evaluator-ready release evidence are
  still pending.

The product work should continue from the canonical graph, while the control-
plane state remains governed by the PRD, Task Master graph, agent config,
skills, and thin durable docs.

## Documentation map

Use `docs/README.md` as the navigation hub. The intended shape is a small
canonical set: `SETUP.md` for bootstrap, `docs/ARCHITECTURE.md` for rationale,
`docs/design/wireframes.md` for evaluator-facing UX, `docs/evaluation/eval-strategy.md`
for eval guidance, `docs/reference/` for stable schemas/context, and
`docs/process/` for validation, delivery flow, and retrospectives.

Important entry points:

- `CHANGELOG.md` — release history and semantic-release target file.
- `SETUP.md` — canonical local bootstrap and operator commands.
- `docs/AGENTS.md` — docs-local decisioning and placement rules.
- `docs/ARCHITECTURE.md` — architecture approach, alternatives, and validation.
- `docs/README.md` — documentation navigation.
- `docs/design/wireframes.md` — evaluator/demo UX flow and evaluator contract.
- `docs/evaluation/eval-strategy.md` — Promptfoo-first eval strategy.
- `docs/reference/context-lineage.md` — source-of-truth, artifact, and retained-context rules.
- `docs/reference/question-packet-schema.md` — question, escalation, and status packet shapes.
- `docs/process/quality-gates.md` — validation ladder.
- `docs/process/retrospective.md` — recurring lesson capture and promotion rules.
- `docs/process/sdlc.md` — branch, PR, and release flow.
- `scripts/cleanup_transient_artifacts.sh` — optional local cleanup for ignored reports and caches.

## Required local setup

Keep secrets and provider config out of source. Use local shell, password manager, user-level tool config, or CI secrets.

```bash
npm ci
uv sync --all-groups
uvx --from code-review-graph code-review-graph --version
uvx --from semgrep semgrep --version
uv tool install -p 3.13 serena-agent
codex doctor --summary --ascii --no-color
```

Task Master runtime setup is local-only:

```bash
cp .taskmaster/config.example.json .taskmaster/config.json
npx --yes --package task-master-ai@0.43.1 -c 'task-master models --setup'
```

Do not commit `.taskmaster/config.json` or `.taskmaster/state.json`.

See `.taskmaster/README.md` for the workspace layout and
`.taskmaster/docs/runtime-policy.md` for provider/model profiles, dependency
policy, and required raw evidence after runtime changes.

## Core validation commands

```bash
npm run skills:lint
npm run skills:audit
npm run release:check
npm run deps:tree
npm run workflow:lint
npm run policy:check
npm run security:scan
npm run docs:quality
npm run eval:ci
uv run pytest
uv run python manage.py check
npx --yes --package task-master-ai@0.43.1 -c 'task-master validate-dependencies'
```

## Do not commit or package

- `.env`, `.env.*`, `.mcp.json`, `.taskmaster/config.json`, provider keys, private tokens, OAuth/session state;
- `.codex-local/`, `.rtk/`, `.serena/`, `.repomix/`, `.tokenix/`, `.headroom/`;
- local DBs, generated corpora, embeddings, media uploads, static build output;
- `.venv/`, `node_modules/`, caches, coverage/build artifacts, previous local export archives.
