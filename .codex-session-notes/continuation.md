# Library Ops Continuation

Freshness marker: last refreshed `2026-06-21`. Treat unverifiable items as provisional until re-verified next session.

## Source Order

1. `.specify/memory/constitution.md`
2. `.taskmaster/docs/prd.md`
3. `specs/001-core/*`
4. committed `.taskmaster/tasks/tasks.json`
5. current Task Master task or subtask
6. this handoff note, nested `AGENTS.md`, and `.codex/agents/*.toml`
7. relevant `.agents/skills/*/SKILL.md`
8. consolidated ADRs and supporting docs under `docs/`
9. source code and tests

## Current Handoff Snapshot

- Branch: `release-convergence-20260621` (active local branch for continuation).
- PR: `#28` (open draft, target `development`, current head `3c57bd1`).
- Local branch proof state: latest revalidated PR checks are on prior head `a6a1191` (`commitlint`, `policy`, `quality`, `security`, `workflow-security`; CI run `27887454334`, commitlint run `27887454337`). Follow-on local head `3c57bd1` is not yet revalidated in this handoff cycle.
- Current PR state in this file is constrained to local git evidence only: branch/head are read from `git status`, `git rev-parse`, and `git log`.
- Control-plane truth updates (local evidence):
  - `2126fcc` (`docs(release): realign release-truth surfaces`): updated continuation, README, PRD, specs, and docs quality-gate wording to current release-convergence intent.
  - `8c65587` (`docs(control-plane): harden taskmaster mutation policy`): hardened mutation posture in `.taskmaster/AGENTS.md`, `.taskmaster/docs/runtime-policy.md`, `.taskmaster/README.md`, `.agents/skills/taskmaster/SKILL.md`, `.codex/agents/coordinator.toml`, `.codex/config.toml`, and governance tests.
  - `.taskmaster/tasks/tasks.json` line 3508 now records drift root cause as stale Task Master reads + non-canonical mutation/refresh paths and the required wait/capture path (Task Master note, then MCP/CLI mutation path when fresh).
- Major completed slices to carry forward:
  - pre-push authority
  - planning/spec reconciliation
  - auth provider parity
  - exact-identifier UI
  - archive confirmation
  - circulation boundary split
  - circulation lookup
  - circulation dashboard reflow
  - cast cleanup
  - PostgreSQL proof
  - search accessibility proof
  - AI-remnant prune
  - Spark-default control-plane packet
- External blocker: `16.6` remains blocked on provider-console / Render deployment / Site(SocialApp) configuration.
- Remaining local governance queue to keep explicit but out of the merge blocker list:
  - `14.6` milestone-board checkpointing and evidence capture
  - `14.7` post-merge local branch/worktree/stash cleanup
  - `14.11` keep tiny hygiene slices off the coordinator root
- Remaining active queue under PR pressure:
  - `16.6` external proof blocker only
- Dependabot queue (`15.*`) remains separate from this handoff queue and should stay out of PR `#28`.
- Local validation proof on `2026-06-21`: `checks:prepush`, `taskmaster:validate`, `verify:core`, and `verify:all` all passed when rerun with writable UV/XDG temp roots under `/tmp`; use that env override for future `uvx` / Semgrep-based gate reruns in this environment.
- Keep this file concise, evidence-first, and this branch/PR as the current coordination root.

## Carry Forward

- Re-check live Task Master/task graph before assuming unverified assumptions.
- Keep work in coordinator-first, Spark-first slices with bounded ownership.
- For any remaining delegated slice on this branch, declare fork vs fresh-spawn
  status, name the inherited context, state expected commit scope plus local
  gates before push, and move overlapping write scopes into separate worktrees
  before the diffs entangle.
- Preserve notice-only stop-hook expectations unless repo surfaces are changed.
