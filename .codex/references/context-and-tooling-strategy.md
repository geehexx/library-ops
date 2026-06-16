# Context and tooling strategy reference

Use this file as the compact agent-facing summary of the active Codex operating
posture for Library Ops.

## Active posture

- root coordinator plus direct specialists by default;
- `agents.max_depth = 1` unless explicitly re-enabled with evidence;
- `gpt-5.4` for root synthesis and `gpt-5.4-mini` for read-heavy specialist work;
- Task Master MCP runs on the custom minimal set
  `get_tasks,next_task,get_task,set_task_status,update_subtask,parse_prd`,
  while heavier graph analysis, regeneration, and mutation stay on the CLI;
- use Serena, code-review-graph, and ast-grep before broad source edits.

## Required verification

```bash
codex doctor --summary --ascii --no-color
npx --yes --package task-master-ai@0.43.1 -c 'task-master validate-dependencies'
npm run checks:precommit
npm run verify:core
```
