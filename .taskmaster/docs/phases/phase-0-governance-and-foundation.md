# Library Ops Phase 0 PRD View

Canonical source: `.taskmaster/docs/prd.md`

## Goal

Finish governance, repository foundation, toolchain readiness, Codex/MCP
configuration, and parseable planning artifacts.

## Includes

- Capability `C1 Project Foundation`
- PRD sections on source-of-truth order, standards profile, agent/MCP workflow,
  CI/CD, and verification posture
- Task Master/Spec Kit/runtime-policy alignment needed before product work

## Exit criteria

- control-plane package verification passes
- PRD parses cleanly for the selected provider lane
- Task graph has no circular dependencies
- CI/governance skeleton is accurate

## Suggested local regeneration command

```bash
npx --yes --package task-master-ai@0.43.1 -c 'task-master parse-prd .taskmaster/docs/phases/phase-0-governance-and-foundation.md --force'
```
