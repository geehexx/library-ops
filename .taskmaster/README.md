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
- `.taskmaster/config.example.json`
  is the committed starter shape for local-only `.taskmaster/config.json`.
- `.taskmaster/AGENTS.md`
  holds Task Master-specific execution rules.

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
