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
- PR: `#28` (open, target `development`).
- Local branch head currently includes commits through `ad3665d`; remote PR head remains monitored by the DevOps owner.
- Live PR checks: all lanes green except `quality` (running/pending or unresolved).
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
- External blocker: `16.6` remains blocked on provider-console / Render host / Site(SocialApp) configuration.
- Remaining active queue under PR pressure:
  - `14.9`
  - `16.1`
  - `15.*` reconciliation
  - `16.20`
  - `16.3`
  - `16.6` external proof blocker
- Dependabot queue remains separate from this handoff queue.
- Keep this file concise, evidence-first, and this branch/PR as the current coordination root.

## Carry Forward

- Re-check live Task Master/task graph before assuming unverified assumptions.
- Keep work in coordinator-first, Spark-first slices with bounded ownership.
- Preserve notice-only stop-hook expectations unless repo surfaces are changed.
