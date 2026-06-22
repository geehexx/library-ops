---
name: speckit-taskmaster-bridge
description: Use when aligning Spec Kit artifacts, community presets, Task Master PRD content, and generated task graph.
---

# Spec Kit ↔ Task Master Bridge

## Purpose

Keep Spec Kit and Task Master aligned without creating competing sources of truth.

## Rules

1. Constitution is governance.
2. `docs/PRD.md` is canonical execution PRD.
3. Spec Kit specs/plans/tasks are supporting planning artifacts.
4. Community presets require source review before installation.
5. If Spec Kit and Task Master disagree, update PRD/ADR first, then regenerate tasks.

## Preset decision process

For each preset:
- purpose
- templates/commands/scripts
- relevance
- security risk
- install/adapt/reject decision
- ADR impact

## Output

- Alignment status:
- Conflicts:
- Presets recommended:
- Presets rejected:
- Required PRD/ADR updates:
