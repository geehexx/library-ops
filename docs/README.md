# Documentation map

The docs tree uses Diátaxis categories and keeps durable decisions separate from operational guidance.

| Need | Location | Purpose |
|---|---|---|
| Tutorials | `tutorials/` | Learning paths when needed. |
| How-to | `how-to/`, `setup/`, `runbook.md` | Task-oriented setup and operation. |
| Reference | `reference/`, `adr/`, `process/quality-gates.md` | Stable facts, schemas, matrices, policies. |
| Explanation | `explanation/`, `architecture/`, `decisioning/` | Rationale, tradeoffs, alternatives. |

Start with `../README.md`, `../AGENTS.md`, and `runbook.md`. Keep polished
human-facing guidance in this docs tree and keep executable agent context in
the canonical source-of-truth files under the repo root, `.codex/`,
`.taskmaster/`, and `.agents/skills/`.

High-signal paths for the current repo state:

- `../CHANGELOG.md`
- `how-to/run-promptfoo-suites.md`
- `how-to/evaluator-demo.md`
- `process/sdlc.md`
