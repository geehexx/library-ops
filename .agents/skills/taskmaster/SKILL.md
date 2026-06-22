---
name: taskmaster
description: Use when starting, inspecting, updating, expanding, validating, or completing Task Master tasks for the project.
---

# Task Master Skill

## Purpose

Use Task Master as the execution graph.
Treat acceptance criteria, test quality, and pass/fail evidence as required inputs before marking done.
Long-horizon goals stay broad and outcome-based. Any implementable work must
be captured in Task Master before implementation begins.
Batch reasoning before tools: confirm dependencies, PRD links, and acceptance
criteria before the first expansion or implementation pass.

This repo does not use Task Master in isolation. Pair it with:

- Context7 for version-specific docs when task details depend on current APIs.
- Exa for broader current research when PRD/spec assumptions need checking.
- Serena for symbol-aware retrieval before updating tasks that point at code.
- code-review-graph for blast radius when graph updates affect implementation
  sequencing or tests.

## Workflow

1. Run or request `task-master next`.
2. Inspect with `task-master show <id>`.
3. Confirm dependencies, PRD links, and acceptance criteria. If the task is already a bounded quick fix, single-file edit, or debugger slice, do not reopen whole-graph planning; move straight to the smallest owned subtask. If test-quality expectations or pass/fail evidence are unclear, route through `$clarify-and-goal` before expanding.
4. If task is broad, run `task-master expand --id=<id> --research`.
5. Implement or delegate one bounded subtask. If it can finish in one Spark
   pass, ask for the patch, validation, and return envelope in that single
   milestone instead of splitting the work into extra JIT turns.
   If the same Spark fork still has the right context, keep it alive across turns instead of closing and reopening it mid-slice.
   If the slice branches, keep the parent owned by the coordinator or
   specialist and delegate a bounded child worker instead of widening the
   local pass.
6. Update task notes with files changed, checks run, milestone reached,
   acceptance-criteria status, pass/fail evidence, risks, and remaining work.
   When new findings or follow-on slices appear, add or update the relevant
   task, subtask, or note before implementation instead of widening the goal.
7. Mark done only when acceptance criteria and checks pass with pass/fail evidence recorded.
8. If the subtask is blocked on a decision or another agent-owned slice, stop,
   record the blocker, and return an Escalation packet instead of branching into
   adjacent work.
9. If a branch is force-pushed, replaced, or superseded, refresh the relevant
   checks and mergeability evidence against the current head before marking the
   task done.

## Library Ops MCP posture

- Active `TASK_MASTER_TOOLS` mode is a custom minimal set:
  `get_tasks,next_task,get_task,set_task_status,update_subtask,parse_prd`.
- Keep these in MCP because they are the high-frequency interactive operations:
  graph inspection, next-task lookup, status changes, durable notes, and PRD
  parsing when the result needs to stay in the interactive loop.
- Route heavier or noisier Task Master operations through the CLI:
  `analyze-complexity`, `complexity-report`, `expand`, `expand --all`,
  `add_task`, `add_subtask`, `remove_task`, `generate`, and model tuning.
- Use the Task Master notes to record when a slice was intentionally kept
  narrow so future runs do not repeat the same JIT planning.
- Record when a delegated slice intentionally stayed within one pass, and
  note the milestone boundary that should trigger the next review.
- The committed local-first runtime profile is defined by the repo-local
  Task Master and Codex config surfaces. Prefer proving bounded local
  operations first, then escalate to a remote rescue provider only when the
  local lane cannot satisfy the required task.
- If a Task Master operation depends on current framework or provider behavior,
  fetch the current docs first instead of letting the model improvise.
- Never hand-edit `.taskmaster/tasks/tasks.json` or force-regenerate it as a
  workaround for stale reads. If the canonical writer path is stale or unavailable,
  stop, record the blocker in Task Master, and use the MCP/CLI mutation path
  once the source of truth is fresh again.
- Treat the `master` surface as the canonical committed view for this repo
  session. Alternate tag surfaces are staged snapshots and only become
  mutation targets when the Task Master note explicitly records that intent.
- Do not use forceful PRD regeneration against the committed graph as a
  routine refresh. Review the current graph first, prefer notes/status updates
  for narrow continuation work, and treat graph replacement as an explicit
  regeneration event that must be justified in Task Master instead of a
  convenience command.

## Prohibited

- Do not manually edit `.taskmaster/state.json`.
- Do not implement work outside the task graph.
- Do not mark tasks done based only on code changes.

## Output

- Current task:
- Scope:
- Acceptance criteria:
- Pass/fail evidence:
- Dependencies:
- PRD/ADR links:
- Implementation plan:
- Required checks:
- Task update needed:
