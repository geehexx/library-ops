# Package manifest

This is a governed Codex CLI control-plane package for Library Ops.

## Canonical content

- `AGENTS.md` and nested `AGENTS.md` files.
- `.codex/config.toml`, `.codex/agents/`, hooks, and rules.
- `.agents/skills/`, including `clarify-and-goal`.
- `.taskmaster/docs/prd.md` and Task Master template.
- `.specify/` and `specs/001-core/`.
- `docs/`, including clarification, goal, quality, evidence, and handoff docs.
- CI, policy, scripts, package/lock files, and minimal Django bootstrap.

## Derived/operator-local content not included

Generated Task Master runtime state, MCP credentials, local caches, graph databases, Repomix packs, Promptfoo outputs, virtualenvs, `node_modules`, imported corpora, media, embeddings, and local databases.
