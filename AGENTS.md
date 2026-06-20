# AGENTS.md

## Mission

Build **Library Ops** from the canonical PRD/spec pack and derived Task Master
graph using a coordinator-first Codex workflow, explicit specialist routing,
and the required local toolchain. Long-horizon goals stay broad and
outcome-based. Any implementable work must be captured in Task Master before
implementation begins.

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

Long-horizon goals stay broad and outcome-based. Any implementable work must
be captured in Task Master tasks and subtasks before implementation begins.

## Coordinator-default contract

- The interactive root agent is always the coordinator by default.
- Do not rely on a hidden `default-agent` setting to enforce that posture.
- Prefer direct specialists for bounded work; keep the root focused on
  coordination and synthesis. If a slice is already narrow enough for a
  Spark lane or another specialist, delegate it instead of re-planning it at
  the root.
- If a specialist already owns a slice, wait for its return or an explicit
  scope change instead of reclaiming it early.
- Depth-2 delegation is allowed only when the root explicitly assigns a
  bounded sub-specialist chain. The root remains the only interactive
  coordinator and final decision owner.
- Discovery is mandatory by default: start with skill discovery, then route
  the slice to the narrowest specialist or subagent before broad root-local
  tool use. If the root can keep widening the search, treat that as a
  coordination defect and stop widening.
- Route explicit command work, local evidence gathering, and bounded
  implementation to the Spark micro-workers first: `command_runner` for
  commands and quick fixes, `context_gatherer` for local evidence and
  debugger passes, `single_file_implementer` for one-file quick fixes, and
  `implementer` for small multi-file implementation slices. Use
  `researcher` / `docs_researcher` for source-backed lookups and summary when
  the slice needs research.
- Batch reasoning before tools: sketch the likely branch points and evidence
  needs first, then issue the narrowest delegated or shell pass.
- If context is thin, do not widen root-local tool use. Build a prescriptive
  delegate packet that names the Spark lane or specialist, the matching
  repo-local skill, the owned files or modules, and the evidence expected
  back.
- Default to Spark-first delegation for trivial or noisy work. Reuse a live agent
  by forking the existing history when the next path can share context and keep
  the same role/model; spawn a clean agent when the role or model should
  change.
- When writing a delegate packet, say explicitly whether it is a fork or a
  fresh spawn, name the inherited context, prefer reuse over close+respawn,
  split overlapping slices into separate worktrees before conflicts appear,
  and include the expected commit scope plus local gate list before push.
- When new findings or follow-on slices appear, capture them in Task Master
  tasks, subtasks, or notes before implementation instead of widening the
  goal.
- Treat repeated JIT replanning as a smell. Once the task shape is known, keep
  the slice bounded and let the delegated agent return evidence or a blocker.
- Ask subagents for compact envelopes: `status`, `evidence`, `gaps`,
  `next_step` or an equivalent short structure. Bubble-up reports should be
  brief, evidence-backed, and free of narrative padding or token waste.
- Keep thread headroom available by closing completed agents promptly and
  reusing live agents by role before spawning another one. A saturated pool is
  a process defect, not a reason to absorb the work back into the root.
- Use `scripts/codex-runtime-env.sh` for cache-sensitive commands when you
  want controlled cache roots or predictable tool state.
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
   under `.agents/skills/`, read the relevant `SKILL.md` entrypoint directly
   before any symbol/context tooling, then choose the skill whose capability
   and trigger best match the task. Do not use Serena memory reads, stale
   rollout notes, or other proxy discovery paths as a substitute for selecting
   the skill entrypoint. Prefer explicit skill workflows over ad hoc
   repetition and stop at ownership boundaries instead of widening scope
   locally.
6. Use `/plan`, native question routing, and `/goal` according to
   `.agents/skills/clarify-and-goal/SKILL.md`.
7. Use Serena, code-review-graph, and repo-local ast-grep before broad source
   changes. Use `npm run astgrep:scan` or `npm exec -- ast-grep ...`, not a
   guessed global binary.
8. Use RTK for noisy exploration and raw output for exact evidence.
9. Record decisions, evidence, and validation in Task Master notes.

Startup handoff contract:
- Repository startup and stop paths are controlled by `.codex/hooks/session_start_notice.py`, `.codex/hooks/session_stop_notice.py`, and `.codex/hooks.json`.
- Stop-hook behavior is notice-only and must output valid JSON to continue the stop flow.
- Do not re-ask for known defaults (workspace/default/operator context) when those defaults are already captured in repo surfaces or explicitly confirmed by the user.

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
- When a second path can reuse the same context and should stay on the same
  role/model, prefer forking the live history over a clean spawn. Only create a
  new agent when the role or model should differ.
- Do not duplicate or reclaim active owned slices early; wait for the owner to
  return, block, or hand back scope.
- When combining slices or worktrees, force an explicit checkpoint review
  before merging them together: inspect both diffs, confirm ownership overlap,
  and verify the changed test surface instead of assuming the join is clean.
- Prefer waiting or blocked status over silent local takeover when the critical
  path belongs to a specialist.
- Treat root absorption of broad implementation after delegation as a process
  defect that should be corrected before closeout.
- If a new slice appears, update the relevant Task Master task, subtask, or
  note instead of widening the goal.
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

Use the canonical gate ladder in `docs/process/quality-gates.md`.

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
- When a pattern proves durable, promote it into the relevant skill or repo
  docs; do not leave it trapped as memory-only guidance.
- Promote repeated lessons into tracked surfaces through
  `docs/process/retrospective.md` instead of letting memory-only instructions
  compound indefinitely.

## Repository hygiene

Never commit secrets, private MCP state, generated corpora, media, embeddings,
local databases, code graph caches, Repomix output, Promptfoo result exports,
virtualenvs, `node_modules`, or scan artifacts unless explicitly sanitized and
approved.
