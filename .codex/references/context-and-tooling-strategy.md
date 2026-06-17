# Context and tooling strategy reference

Use this file as the compact agent-facing summary of the active Codex operating
posture for Library Ops.

## Active posture

- root coordinator plus direct specialists by default; when the user explicitly
  asks for subagents, assign bounded slices, avoid local takeover of owned
  work, and prefer waiting or blocked states over early rework;
- `agents.max_depth = 1` unless explicitly re-enabled with evidence;
- `gpt-5.4` for root synthesis and `gpt-5.4-mini` for read-heavy specialist work;
- Task Master MCP runs on the custom minimal set
  `get_tasks,next_task,get_task,set_task_status,update_subtask,parse_prd`,
  while heavier graph analysis, regeneration, and mutation stay on the CLI;
- use Serena, code-review-graph, and repo-local ast-grep before broad source
  edits;
- For Python and Django changes, treat Pyright as the first static check on the touched scope before wider pytest or gate runs.

## Auto-loaded vs manual surfaces

- Keep root `AGENTS.md` as the short coordinator contract only.
- Use nested `AGENTS.md` only for directory-specific rules.
- Put repeatable workflows in skills.
- Put role-specific behavior in `.codex/agents/*.toml`.
- Keep `.codex/references/*` for shared manual reference material, not for long
  always-on instructions that should auto-load by default.

## Repo-local tool and startup paths

- Use repo-local ast-grep via `npm run astgrep:scan` or
  `npm exec -- ast-grep ...`.
- Prefer tracked repo-local launchers and wrappers over hidden global aliases
  when a workflow should be reproducible for other operators.
- Fresh sessions should use `./scripts/codex-coordinator.sh` rather than ad hoc
  shell wrappers.

## Required verification

```bash
codex doctor --summary --ascii --no-color
npx --yes --package task-master-ai@0.43.1 -c 'task-master validate-dependencies'
npm run checks:precommit
npm run verify:core
```
