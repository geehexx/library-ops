# Task Master agent rules

- `.taskmaster/docs/prd.md` is canonical Task Master input.
- `.taskmaster/tasks/tasks.json` is the committed derived execution graph.
- `.taskmaster/config.json` and `.taskmaster/state.json` are local-only.
- Runtime/provider/dependency policy lives in
  `.taskmaster/docs/runtime-policy.md`.
- Task mutations should use Task Master tools or CLI commands, not manual edits
  to runtime files.
- Task Master work in this repo assumes Context7, Exa, Serena, and
  code-review-graph are available as companion tools for current docs, current
  research, symbol retrieval, and repo-alignment checks.
- `TASK_MASTER_TOOLS=standard` is the active default for Library Ops because
  graph repair and regeneration require more than the lean/core read path.
- Subagent task blockers must be recorded as Escalation packets.
- Do not mark tasks done while a Question packet remains unanswered.
