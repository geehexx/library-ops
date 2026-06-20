---
name: prd-architect
description: Use when creating or revising the canonical PRD, capability tree, dependencies, acceptance criteria, or task decomposition.
---

# PRD Architect Skill

## Purpose

Create and maintain a Task Master-friendly RPG PRD.

## Required PRD qualities

- Separates functional WHAT from structural HOW.
- Uses capabilities as top-level task candidates.
- Uses features as subtask candidates.
- Defines explicit dependencies and phases.
- Includes explicit acceptance criteria, pass/fail evidence, tests, risks, ADRs, and source register.
- Keeps sections navigable and avoids duplicate docs.

## Process

1. Identify the changed decision or feature.
2. Update capability tree and dependency graph.
3. Update acceptance criteria, test strategy, and pass/fail evidence.
4. If test-quality expectations are ambiguous, route them through `$clarify-and-goal` before finalizing.
5. Update ADR register if architecture/process significant.
6. Check Task Master parsing implications.

## Output

- Proposed PRD patch:
- Dependency impact:
- Task Master impact:
- ADR impact:
- Open questions:
