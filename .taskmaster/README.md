# Task Master Workspace

This directory is the repo-owned home for Task Master inputs, derived graph
state, and runtime policy.

## Start here

- `.taskmaster/docs/prd.md`
  is the canonical Task Master input.
- `.taskmaster/tasks/tasks.json`
  is the committed derived execution graph.
- `.taskmaster/docs/runtime-policy.md`
  owns provider/model profiles, commit rules, and runtime evidence policy.
- `.taskmaster/docs/phases/*.md`
  are bounded derived PRD views for local-model regeneration and expansion.
- `.taskmaster/config.example.json`
  is the committed starter shape for local-only `.taskmaster/config.json`.
- `.taskmaster/AGENTS.md`
  holds Task Master-specific execution rules.

For Library Ops, treat Task Master as an essential MCP surface plus companion
tools rather than a standalone generator:

- Context7 for current framework/library documentation
- Exa for current broader research and counter-evidence
- Serena for symbol-aware repo alignment
- code-review-graph for blast-radius checks

## Commit policy

Committed:

- `.taskmaster/AGENTS.md`
- `.taskmaster/config.example.json`
- `.taskmaster/docs/prd.md`
- `.taskmaster/docs/runtime-policy.md`
- `.taskmaster/templates/rpg-prd-template.md`
- `.taskmaster/tasks/tasks.json`

Local-only, never commit:

- `.taskmaster/config.json`
- `.taskmaster/state.json`
- `.taskmaster/tasks/*.md`
- `.taskmaster/reports/`

## Common commands

```bash
cp .taskmaster/config.example.json .taskmaster/config.json
npx --yes --package task-master-ai@0.43.1 -c 'task-master models --setup'
npx --yes --package task-master-ai@0.43.1 -c 'task-master models'
npx --yes --package task-master-ai@0.43.1 -c 'task-master parse-prd .taskmaster/docs/prd.md --research'
npx --yes --package task-master-ai@0.43.1 -c 'task-master list'
npx --yes --package task-master-ai@0.43.1 -c 'task-master analyze-complexity --research'
npx --yes --package task-master-ai@0.43.1 -c 'task-master expand --all --research'
npx --yes --package task-master-ai@0.43.1 -c 'task-master validate-dependencies'
npx --yes --package task-master-ai@0.43.1 -c 'task-master next'
```

The active MCP mode in `.codex/config.toml` should stay on the custom minimal
set:

- `get_tasks`
- `next_task`
- `get_task`
- `set_task_status`
- `update_subtask`
- `parse_prd`

Everything heavier stays on the pinned CLI:

- complexity analysis and reporting
- task expansion
- bulk task creation/removal
- task file generation
- model/provider tuning

For local-model work, prefer phase PRDs over the monolithic PRD when you need a
smaller, better-bounded generation target. Do not treat the phase PRDs as a
reason to overwrite the committed graph in place. Review graph changes in a
bounded lane first, and avoid `task-master parse-prd --force` on repo-owned
surfaces unless the owning Task Master task explicitly calls for graph
replacement.

Current proven low-memory local lane:

- main: `qwen2.5-coder:7b-instruct`
- research: `qwen2.5-coder:7b-instruct`
- fallback: `qwen3:latest`

That lane is proven for bounded PRD parsing on this machine. Keep remote
providers as explicit rescue options, not as the committed default.
