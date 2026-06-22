# Library Ops Phase 0 PRD View

Canonical source: `docs/PRD.md`

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

## Suggested local regeneration workflow

Review the committed graph first. If phase-0 regeneration is genuinely needed,
run it as a bounded draft/review lane and compare the result against
`.taskmaster/tasks/tasks.json` before accepting any mutations. Do not use
`task-master parse-prd --force` here as a routine refresh.
