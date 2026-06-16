# Task Master agent rules

- `.taskmaster/docs/prd.md` is canonical Task Master input.
- `.taskmaster/tasks/tasks.json` is the committed derived execution graph.
- `.taskmaster/config.json` and `.taskmaster/state.json` are local-only.
- Runtime/provider/dependency policy lives in
  `.taskmaster/docs/runtime-policy.md`.
- Task mutations should use Task Master tools or CLI commands, not manual edits
  to runtime files.
- Subagent task blockers must be recorded as Escalation packets.
- Do not mark tasks done while a Question packet remains unanswered.
