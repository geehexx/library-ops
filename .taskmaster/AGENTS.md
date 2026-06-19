# Task Master agent rules

- `.taskmaster/docs/prd.md` is canonical Task Master input.
- `.taskmaster/tasks/tasks.json` is the committed derived execution graph.
- Long-horizon goals stay broad and outcome-based. Any implementable work must
  be captured in Task Master before implementation begins.
- `.taskmaster/config.json` and `.taskmaster/state.json` are local-only.
- Runtime/provider/dependency policy lives in
  `.taskmaster/docs/runtime-policy.md`.
- Task mutations should use Task Master tools or CLI commands, not manual edits
  to runtime files.
- When new findings or follow-on slices appear, add or update the relevant
  task, subtask, or note before implementation instead of widening the goal.
- Task Master work in this repo assumes Context7, Exa, Serena, and
  code-review-graph are available as companion tools for current docs, current
  research, symbol retrieval, and repo-alignment checks.
- The active Task Master MCP surface is a custom minimal set:
  `get_tasks,next_task,get_task,set_task_status,update_subtask,parse_prd`.
- Heavy graph operations such as complexity analysis, expansion, bulk task
  creation/removal, and file generation route through the pinned CLI instead of
  the MCP surface to keep interactive context leaner while preserving full
  functionality.
- The committed example runtime profile is the default local path:
  `qwen2.5-coder:7b-instruct` as main/research and `qwen3:latest` as fallback.
  Use remote providers when they are the better fit for the slice or when the
  local path cannot prove the required operation.
- Subagent task blockers must be recorded as Escalation packets.
- Do not mark tasks done while a Question packet remains unanswered.
