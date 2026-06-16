# Documentation map

The docs tree uses Diátaxis categories and keeps durable decisions separate from operational guidance.

| Need | Location | Purpose |
|---|---|---|
| Tutorials | `tutorials/` | Learning paths when needed. |
| How-to | `how-to/`, `setup/`, `runbook.md` | Task-oriented setup and operation. |
| Reference | `reference/`, `adr/`, `process/quality-gates.md` | Stable facts, schemas, matrices, policies. |
| Explanation | `explanation/`, `architecture/`, `decisioning/` | Rationale, tradeoffs, alternatives. |

Start with `../README.md`, `../AGENTS.md`, `agent-system/clarification-and-goals.md`, and `runbook.md`. Keep durable operating context in this docs tree and the canonical source-of-truth files, not in one-off handoff artifacts.

High-signal paths for the current repo state:

- `../CHANGELOG.md`
- `how-to/run-promptfoo-suites.md`
- `how-to/figma-mcp-login.md`
- `how-to/evaluator-demo.md`
- `reference/context-lineage.md`
- `process/sdlc.md`
