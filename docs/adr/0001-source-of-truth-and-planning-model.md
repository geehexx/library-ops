# ADR-0001: Source of truth and planning model

- Status: accepted
- Date: 2026-06-13
- Deciders: Andrew Crozier

## Context

The project is both an interview demo and a Codex-driven implementation workspace. It needs enough governance to prevent agent drift without turning every note into a competing source of truth. The earlier ADR set split related planning decisions into many small records, which increased navigation cost for both humans and agents.

## Decision

Use the following source-of-truth order:

1. `.specify/memory/constitution.md` for immutable project principles and governance rules.
1. `.taskmaster/docs/prd.md` for product scope, requirements, acceptance criteria, task-generation hints, and current accepted constraints.
1. `specs/001-core/*` for supporting Spec Kit consistency, implementation plan, data model, contracts, quickstart, and task breakdown.
1. Task Master generated tasks for execution order after `task-master parse-prd` and complexity analysis.
1. The current Task Master task/subtask.
1. `AGENTS.md`, nested `AGENTS.md`, and `.codex/agents/*.toml`.
1. `.agents/skills/*/SKILL.md`.
1. ADRs and supporting docs for architecturally significant decisions, research, quality gates, runbooks, tool alternatives, and design details.
1. Source code and tests as final executable truth.

Task Master and Spec Kit are complementary, not redundant: Task Master owns dependency-aware execution; Spec Kit owns spec/plan/task consistency. The repo may keep seed tasks before Task Master runs, but generated tasks must be reviewed against the seed, not without review accepted.

## Alternatives considered

| Alternative | Benefit | Rejected or adapted because |
|---|---|---|
| PRD only | Smallest Task Master input surface | Too much rationale and architecture context would pollute the PRD. |
| Spec Kit only | Strong spec-driven workflow | Does not replace Task Master’s execution graph and task commands. |
| Many narrow ADRs | Low friction for incremental edits | Too noisy for this repo; many earlier ADRs were policy notes, not architecturally significant decisions. |
| Wiki-style docs everywhere | Flexible | Agents may treat stale notes as equal to the PRD. |

## Consequences

- ADR count is intentionally small and consolidated.
- The PRD stays parseable and human-reviewable.
- Long rationale belongs in supporting docs and ADRs, not inline in every PRD section.
- Agents must update the right layer when a requirement, decision, plan, or implementation changes.

## Validation

- Source-of-truth drift is checked by keeping the file set small, reviewing the higher-priority artifacts first, and avoiding duplicate verifier-era process layers.
- Task Master flow: parse PRD, list/review tasks, analyze complexity, expand tasks, then implement the next task.
- Spec Kit flow: keep spec/plan/tasks aligned before `/speckit.implement`-style execution.
