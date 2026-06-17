# AGENTS.md

## Mission

Build **Library Ops** from the canonical PRD/spec pack and derived Task Master
graph using a coordinator-first Codex workflow, explicit specialist routing,
and the required local toolchain.

## Source-of-truth order

1. `.specify/memory/constitution.md`
2. `.taskmaster/docs/prd.md`
3. `specs/001-core/*`
4. committed `.taskmaster/tasks/tasks.json`
5. current Task Master task/subtask
6. this file, nested `AGENTS.md`, and `.codex/agents/*.toml`
7. relevant `.agents/skills/*/SKILL.md`
8. consolidated ADRs and supporting docs under `docs/`
9. source code and tests

## Coordinator-default contract

- The interactive root agent is always the coordinator by default.
- Do not rely on a hidden `default-agent` setting to enforce that posture.
- Spawn direct specialists for bounded work; do not let the root absorb broad
  implementation or recursive fan-out by habit.
- Keep root `AGENTS.md` lean. Shared clarification, escalation, tooling, and
  continuation mechanics belong in:
  - `.codex/references/clarification-and-goals.md`
  - `.codex/references/context-and-tooling-strategy.md`
  - `.codex/agents/*.toml`
  - repo-local skills under `.agents/skills/`

## Required session start

1. Read the current task and linked PRD/spec section. If the task graph does
   not yet exist, read the constitution, canonical PRD, and `specs/001-core/*`
   first.
2. Check `git status`.
3. Confirm whether the work is meta/control-plane, product-code, or both; split
   commits accordingly.
4. Confirm the canonical continuation artifacts:
   - `.codex-session-notes/continuation.md` is authoritative
   - `.codex-session-notes/scratch.md` is optional scratch only
5. Perform skill discovery before broad work. Start with the repo-local catalog
   under `.agents/skills/`, then installed/global skills. Prefer explicit skill
   workflows over ad hoc repetition.
6. Use `/plan`, native question routing, and `/goal` according to
   `.codex/references/clarification-and-goals.md`.
7. Use Serena, code-review-graph, and repo-local ast-grep before broad source
   changes. Use `npm run astgrep:scan` or `npm exec -- ast-grep ...`, not a
   guessed global binary.
8. Use RTK for noisy exploration and raw output for exact evidence.
9. Record decisions, evidence, and validation in Task Master notes.

## Routing rules

- Route Python/Django implementation through `$django-feature`.
- Route code/context/tooling questions through `$code-intelligence`.
- Route ambiguity, question packets, and goal shaping through
  `$clarify-and-goal` and `$define-goal` when appropriate.
- Route routine Task Master mutation through `taskmaster_governor`; root may
  write directly only with an explicit note explaining why.
- Do not rely on `skills.config` overrides as if they guarantee always-loaded
  behavior. Use explicit routing, trigger text, and prompt-level invocation.

## Delegation and escalation

- When the user explicitly asks for subagents, root must delegate bounded slices
  with a clear owner and return condition.
- Do not duplicate or reclaim active owned slices early.
- Prefer waiting or blocked status over silent local takeover when the critical
  path belongs to a specialist.
- Question and Escalation packet formats, remote-policy blocker handling, and
  native user-input routing live in `.codex/references/clarification-and-goals.md`.

## Required local checks

Use these entry points:

```bash
codex doctor --summary --ascii --no-color
npx --yes --package task-master-ai@0.43.1 -c 'task-master validate-dependencies'
npm run checks:precommit
npm run verify:core
npm run verify:all
```

For the current detailed validation ladder, read:

```bash
sed -n '1,220p' docs/process/quality-gates.md
```

## Coordinator-first launcher

Use the tracked repo-local launcher for fresh sessions:

```bash
./scripts/codex-coordinator.sh
```

If you want a shell alias, point it at that tracked script rather than hiding
workflow logic in untracked global wrappers.

## Continuation and retrospective

- Keep `.codex-session-notes/continuation.md` updated at major checkpoints.
- Treat `.codex-session-notes/scratch.md` as disposable working notes only.
- Promote repeated lessons into tracked surfaces through
  `docs/process/retrospective.md` instead of letting memory-only instructions
  compound indefinitely.

## Repository hygiene

Never commit secrets, private MCP state, generated corpora, media, embeddings,
local databases, code graph caches, Repomix output, Promptfoo result exports,
virtualenvs, `node_modules`, or scan artifacts unless explicitly sanitized and
approved.
