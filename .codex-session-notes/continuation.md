# Library Ops Continuation

Freshness marker: last refreshed `2026-06-21`. Treat unverifiable items as provisional next session.

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

- PR `#26` is merged into `development`.
- Branch `recovery/clean-landing-tm11-20260620` currently contains unpushed local continuation work; re-check `git status --short --branch` before assuming the exact ahead count or local head list.
- The current local continuation tranche includes the pre-push authority commit, the release-convergence planning reconciliation commit, and this handoff refresh series.
- Active release-convergence queue:
  - `14.9` local-vs-CI gate authority model
  - `15.4` dependency closure against that model
  - `16.1` canonical truth sweep
  - `16.15` delegation packet tightening
  - `16.20` pre-push gatekeeper protocol consuming `14.9` and `16.15`
- UX/search sequencing currently linked to:
  - `16.11 -> 16.7/16.14`
  - `16.18 -> 16.13/16.17`
  - `16.19 -> 16.6`
- Dependabot PR queue remains live and is tracked separately.
- `continuation.md` is still the start-stop handoff authority; keep it brief and evidence-first.

## Carry Forward

- Re-check live Task Master/task graph before assuming unverified assumptions.
- Keep work in coordinator-first, Spark-first slices with bounded ownership.
- Preserve notice-only stop-hook expectations unless repo surfaces are changed.
