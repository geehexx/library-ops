# Library Ops Spec Kit Bridge Override

Use this as a project-local guide when generating Spec Kit specs/plans/tasks.

## Canonical mapping

- Spec Kit constitution -> `.specify/memory/constitution.md`
- Canonical product/execution PRD -> `.taskmaster/docs/prd.md`
- Task execution graph -> Task Master generated tasks
- Spec Kit `spec.md` -> feature-specific requirement artifact
- Spec Kit `plan.md` -> feature-specific implementation plan
- Spec Kit `tasks.md` -> cross-check artifact, not final execution authority

## Generation rules

- Start from committed repo reality before inventing scaffolding work.
- When a spec changes architecture, governance, or external dependencies, note
  the PRD/ADR impact explicitly.
- Keep human docs out of temporary handoff language; durable decisions belong in
  the PRD, ADRs, AGENTS, skills, or concise runbook/setup surfaces.
- Treat Task Master as derived from the canonical PRD and spec pack. If they
  disagree, update PRD/spec first, then regenerate or reconcile the task graph.
- If a spec or plan changes coordinator routing or subagent behavior, preserve
  the delegation rule explicitly instead of softening it into advisory wording.

## Required generated artifact qualities

- Include explicit dependencies.
- Include acceptance criteria.
- Include test strategy.
- Include security/accessibility/search considerations where relevant.
- Include Task Master capability IDs when known.
- Include whether the change belongs to the canonical PRD or to a bounded phase
  PRD view.
- Call out when a local-model-friendly phase slice should be regenerated before
  touching the committed Task Master graph.

## Feature-plan expectations

- `spec.md` should capture the requirement delta, constraints, and user-facing
  acceptance shape for one feature slice, plus explicit deferred scope when the
  branch is intentionally narrower than the full product roadmap.
- `plan.md` should describe the implementation path, touched systems, and
  validation approach without duplicating the whole PRD. For phase-oriented
  work, prefer a clear structure of entry point, current-slice scope, deferred
  scope, and cross-cutting validation.
- `tasks.md` should be small, reviewable, and consistent with the eventual Task
  Master graph rather than acting as a second execution authority.
- If a feature affects governance, runtime policy, or control-plane behavior,
  `plan.md` should explicitly map the change across constitution, PRD,
  Task Master, AGENTS, skills, ADRs, and human docs.
