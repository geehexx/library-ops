---
name: taskmaster
description: Use when starting, inspecting, updating, expanding, validating, or completing Task Master tasks for the project.
---

# Task Master Skill

## Purpose

Use Task Master as the execution graph.

This repo does not use Task Master in isolation. Pair it with:

- Context7 for version-specific docs when task details depend on current APIs.
- Exa for broader current research when PRD/spec assumptions need checking.
- Serena for symbol-aware retrieval before updating tasks that point at code.
- code-review-graph for blast radius when graph updates affect implementation
  sequencing or tests.

## Workflow

1. Run or request `task-master next`.
2. Inspect with `task-master show <id>`.
3. Confirm dependencies and PRD links.
4. If task is broad, run `task-master expand --id=<id> --research`.
5. Implement or delegate one bounded subtask.
6. Update task notes with files changed, checks run, risks, and remaining work.
7. Mark done only when acceptance criteria and checks pass.

## Library Ops MCP posture

- Active `TASK_MASTER_TOOLS` mode is a custom minimal set:
  `get_tasks,next_task,get_task,set_task_status,update_subtask,parse_prd`.
- Keep these in MCP because they are the high-frequency interactive operations:
  graph inspection, next-task lookup, status changes, durable notes, and PRD
  parsing when the result needs to stay in the interactive loop.
- Route heavier or noisier Task Master operations through the CLI:
  `analyze-complexity`, `complexity-report`, `expand`, `expand --all`,
  `add_task`, `add_subtask`, `remove_task`, `generate`, and model tuning.
- The current committed local-first runtime profile uses
  `qwen2.5-coder:7b-instruct` as main/research and `qwen3:latest` as fallback.
  Prefer proving bounded local operations first, then escalate to a remote
  rescue provider only when the local lane cannot satisfy the required task.
- If a Task Master operation depends on current framework or provider behavior,
  fetch the current docs first instead of letting the model improvise.

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
