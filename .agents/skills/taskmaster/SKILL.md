---
name: taskmaster
description: Use when starting, inspecting, updating, expanding, validating, or completing Task Master tasks for the project.
---

# Task Master Skill

## Purpose

Use Task Master as the execution graph.

## Workflow

1. Run or request `task-master next`.
2. Inspect with `task-master show <id>`.
3. Confirm dependencies and PRD links.
4. If task is broad, run `task-master expand --id=<id> --research`.
5. Implement or delegate one bounded subtask.
6. Update task notes with files changed, checks run, risks, and remaining work.
7. Mark done only when acceptance criteria and checks pass.

## Prohibited

- Do not manually edit `.taskmaster/state.json`.
- Do not implement work outside the task graph.
- Do not mark tasks done based only on code changes.

## Output

- Current task:
- Scope:
- Dependencies:
- PRD/ADR links:
- Implementation plan:
- Required checks:
- Task update needed:
