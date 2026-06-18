# Documentation map

The docs tree keeps maintained human guidance in a small canonical set and
pushes agent-operating instructions back into the repo-root surfaces.

| Need | Canonical location |
|---|---|
| Bootstrap and operator commands | `../SETUP.md` |
| Docs-local placement rules | `AGENTS.md` |
| Architecture rationale | `ARCHITECTURE.md` |
| Evaluator-facing design flow | `design/wireframes.md` |
| Evaluation strategy and Promptfoo examples | `evaluation/eval-strategy.md` |
| Stable context and packet schemas | `reference/context-lineage.md`, `reference/question-packet-schema.md` |
| Validation ladder | `process/quality-gates.md` |
| Retrospective lessons | `process/retrospective.md` |
| Branch, PR, and release flow | `process/sdlc.md` |

Start with `../README.md`, `../SETUP.md`, `../AGENTS.md`, and `AGENTS.md`.
Keep this tree human-facing and keep executable agent context in the canonical
source-of-truth files under the repo root, `.codex/`, `.taskmaster/`, and
`.agents/skills/`.

High-signal paths for the current repo state:

- `../CHANGELOG.md`
- `../SETUP.md`
- `AGENTS.md`
- `ARCHITECTURE.md`
- `design/wireframes.md`
- `evaluation/eval-strategy.md`
- `process/quality-gates.md`
- `process/retrospective.md`
- `process/sdlc.md`
- `reference/context-lineage.md`
- `reference/question-packet-schema.md`
