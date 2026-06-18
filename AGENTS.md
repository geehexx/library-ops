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
  implementation or recursive fan-out by habit. If a specialist already owns a
  slice, wait for its return or an explicit scope change.
- Depth-2 delegation is allowed only when the root explicitly assigns a
  bounded sub-specialist chain. The root remains the only interactive
  coordinator and final decision owner.
- Discovery is mandatory by default: start with skill discovery, then route the
  slice to the narrowest specialist or subagent before broad root-local tool
  use. If the root can keep widening the search, it is a coordination defect.
- Broad direct shell or file exploration from the root is gated. Prefer
  specialist packets or `scripts/codex-runtime-env.sh` for cache-sensitive
  commands such as `npm` and `gh` so home-directory cache writes do not become
  sandbox failures.
- Keep root `AGENTS.md` lean. Shared clarification, escalation, tooling, and
  continuation mechanics belong in `.codex/agents/*.toml` and the explicit
  repo-local skill entrypoints under `.agents/skills/`.
- The native question, escalation, and goal-shaping contract lives in
  `.agents/skills/clarify-and-goal/SKILL.md`.
- The tool-routing, evidence, and blast-radius contract lives in
  `.agents/skills/code-intelligence/SKILL.md`.
- Required repo-local MCP servers in `.codex/config.toml` should stay
  `required = true` and `default_tools_approval_mode = "approve"` unless a
  deliberate trust change is recorded.

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
   under `.agents/skills/`, choose the skill whose capability and trigger best
   match the task, then installed/global skills. Prefer explicit skill
   workflows over ad hoc repetition and stop at ownership boundaries instead
   of widening scope locally.
6. Use `/plan`, native question routing, and `/goal` according to
   `.agents/skills/clarify-and-goal/SKILL.md`.
7. Use Serena, code-review-graph, and repo-local ast-grep before broad source
   changes. Use `npm run astgrep:scan` or `npm exec -- ast-grep ...`, not a
   guessed global binary.
8. Use RTK for noisy exploration and raw output for exact evidence.
9. Record decisions, evidence, and validation in Task Master notes.

## Routing rules

- Route Python/Django implementation through the strongest matching Django or
  repo-local application workflow skill.
- Route code/context/tooling questions through the strongest matching
  code-intelligence or repo-tooling workflow skill.
- Route ambiguity, question packets, and goal shaping through the strongest
  matching clarification/goal workflow skill when appropriate.
- Route routine Task Master mutation through `taskmaster_governor`; root may
  write directly only with an explicit note explaining why.
- Do not rely on `skills.config` overrides as if they guarantee always-loaded
  behavior. Use explicit routing, trigger text, and prompt-level invocation.

## Delegation and escalation

- When the user explicitly asks for subagents, root must delegate bounded slices
  with a clear owner and return condition.
- Do not duplicate or reclaim active owned slices early; wait for the owner to
  return, block, or hand back scope.
- Prefer waiting or blocked status over silent local takeover when the critical
  path belongs to a specialist.
- Treat root absorption of broad implementation after delegation as a process
  defect that should be corrected before closeout.
- Do not stop at a merely stable-looking partial point when real blockers are
  absent and the requested end state is still incomplete. If the work is
  blocked on a decision or another agent's owned slice, stop and report the
  block instead of branching into adjacent work.
- Closeout summaries must state:
  - what was actually finished
  - what remains incomplete
  - why work is stopping now
  - whether the stop is due to a real blocker, user stop, or session boundary
- Question and Escalation packet formats, remote-policy blocker handling, and
  native user-input routing live in
  `.agents/skills/clarify-and-goal/SKILL.md`.

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
