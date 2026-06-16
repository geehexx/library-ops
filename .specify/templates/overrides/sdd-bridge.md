# Library Ops Spec Kit Bridge Override

Use this as a project-local guide when generating Spec Kit specs/plans/tasks.

## Canonical mapping

- Spec Kit constitution -> `.specify/memory/constitution.md`
- Canonical product/execution PRD -> `.taskmaster/docs/prd.md`
- Task execution graph -> Task Master generated tasks
- Spec Kit `spec.md` -> feature-specific requirement artifact
- Spec Kit `plan.md` -> feature-specific implementation plan
- Spec Kit `tasks.md` -> cross-check artifact, not final execution authority

## Required generated artifact qualities

- Include explicit dependencies.
- Include acceptance criteria.
- Include test strategy.
- Include security/accessibility/search considerations where relevant.
- Include Task Master capability IDs when known.
