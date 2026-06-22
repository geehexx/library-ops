# RPG PRD Template

Use this only as a local structure reference. The canonical project PRD is
`docs/PRD.md`.

## Required sections

1. Overview, users, success metrics, non-goals, and explicit out-of-scope work.
2. Source-of-truth order and derived-artifact rules.
3. Standards profile: architecture, documentation, testing, and security posture.
4. Ambiguity log with accepted defaults and explicit ask-user gates.
5. Capability tree with `### Capability:` headings and intent-level outcomes.
6. Features with `#### Feature:` headings, acceptance criteria, and test strategy.
7. Data model, architecture views, integration boundaries, and operational assumptions.
8. Quality gates, release/deployment posture, risks, and rollback expectations.
9. Task Master parsing contract, dependency expectations, and completion evidence shape.
10. Source register and durable references for any non-obvious external claims.
11. Local-model execution notes when the PRD is expected to drive Task Master
    generation on constrained hardware.

## Parsing contract

Task Master should treat capability headings as top-level task candidates and
feature headings as subtasks. Each feature should be written so generated tasks
can inherit:

- a user-visible or operator-visible outcome,
- dependencies or sequencing constraints,
- acceptance evidence,
- a concrete test strategy,
- and any PRD/ADR/source-register link needed to keep later implementation grounded.

## Phase-slice guidance

If the canonical PRD is too large for the active local model lane, derive
bounded phase PRDs that:

- preserve the same source-of-truth order,
- include a concise goal,
- define entry criteria,
- define implementation notes and explicit out-of-scope boundaries,
- state their canonical parent,
- define exit criteria,
- include suggested validation commands when the slice is implementation-near,
- and are safe to regenerate without replacing the canonical PRD.

## Library Ops bias

Prefer wording that reflects committed repo reality. If the code already has a
bootstrap or control-plane surface, describe hardening or extension work rather
than regenerating an idealized scaffold.

Prefer explicit evaluator-facing evidence language over generic phrases that
sound stronger than the evidence. If a claim needs words such as "high-signal",
"complete", or "thorough", the PRD should also state the measurable proof
behind that claim.

If the PRD touches coordinator or subagent behavior, state the delegation rule
explicitly: bounded ownership, no duplicate local implementation of active
owned slices, and waiting or blocked status over early takeover.
