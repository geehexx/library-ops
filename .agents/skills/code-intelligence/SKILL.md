---
name: code-intelligence
description: Use when a task mentions RTK, code graph, code-review-graph, Serena, ast-grep, Repomix, MCP tooling, context optimization, token pressure, fan-out, blast radius, symbol retrieval, repo maps, or agent meta-system configuration.
---

# Code Intelligence and Context Optimization

## Purpose

Use this skill to reduce context waste while improving code understanding and evidence quality. The selected local toolchain is required for implementation environments. Missing tools are blockers unless the run is explicitly using the constrained sandbox profile and the limitation is recorded.

Read `references/README.md` when the coordinator needs the current repo-local
source order, tool-routing guidance, or evidence rules for control-plane work.

## Required stack

- RTK for noisy first-pass command output.
- Raw output for exact diagnostics, audits, scanners, and release evidence.
- `code-review-graph` for blast radius and changed-code context.
- Serena for symbol-aware retrieval and refactor planning.
- `ast-grep` for syntax-aware structural search.
- Repomix only for bounded repo packs when graph/symbol paths are insufficient.
- Direct quality/security gates for final proof.

## Decision discipline

Do not stop at “tool exists.” For material changes, return a decision block:

```text
Decision status:
User tie-back:
Alternatives considered:
Counterfactual evidence:
Recommended path:
Validation evidence:
Security/permission impact:
Rollback:
Open user decision:
```

Pause for user input only when the choice changes credentials, cost, hosted/remote code transfer, irreversible repository state, or explicit project scope. Do not pause merely because a local required tool needs to be run, configured, or smoke-tested.

## Tool ladder

1. `code-review-graph` for structure, blast radius, and review focus.
2. Serena for symbol-level understanding.
3. `ast-grep` for syntax-aware search or codemod checks.
4. RTK for noisy exploratory shell work.
5. Raw commands for exact evidence.
6. Repomix only as a bounded fallback.
7. Security/policy gates only as validation, never as a substitute for source review.

## Research evidence ladder

1. Canonical repo docs, current Task Master task, PRD/spec, and local command evidence.
2. Primary upstream docs, standards, release notes, and official repositories.
3. Context7 for version-specific library/API documentation.
4. Exa and web search for current discovery and counter-evidence.
5. Community/anecdotal sources only as hypothesis seeds, not acceptance evidence.
6. Spark summarization only after source URLs, dates, and claims are separated from primary evidence.

When shell inspection is appropriate, batch related reads into a small number of
focused commands. Avoid repetitive one-file shell reads when Serena,
code-review-graph, or one broader shell pass would answer faster with less
context waste.

## RTK rules

- Codex does not get transparent RTK command mutation through a native hook.
- For Codex, efficiency comes from better default scripts, explicit `rtk ...`
  usage for noisy work, and agent instructions that separate noisy exploration
  from exact evidence.
- Use `npm run checks:precommit` for the fast local hygiene path.
- Keep `npm run verify:core` and `npm run verify:all` as the broader proof paths.

Use RTK for first-pass noisy exploration when output volume is the problem. Do
not make RTK the canonical validation command; raw `uv run` / `npm run` reruns
remain required for gates, failures, audit evidence, and release proof.

```bash
rtk git status
rtk pytest
rtk ruff check .
rtk npm run markdownlint
rtk rewrite "npm run docs:quality"
```

Capture raw evidence with the direct repo commands when output is
audit-sensitive:

```bash
uv run pytest -q
uv run ruff check .
npm run docs:quality
gitleaks detect --source . --redact
uvx --from semgrep semgrep scan --config .semgrep.yml
```

## Graph and symbol rules

Run graph or symbol discovery before broad edits:

```bash
uvx --from code-review-graph code-review-graph build
uvx --from code-review-graph code-review-graph status
# Use MCP graph tools for focused blast-radius questions.
serena init
# Project MCP config starts Serena through `.codex/config.toml`.
ast-grep scan
```

Graph or symbol output is planning evidence, not behavioral proof. Always
inspect the underlying files and run tests.

## Repo-pack rules

Use Repomix only with the repo-local config:

```bash
repomix --config repomix.config.json
```

Never commit `repomix-output.*`. Never include secrets, corpora, media,
embeddings, generated caches, or local MCP state.

## Output format

Return:

```text
Decision status:
User tie-back:
Problem solved:
Alternatives considered:
Counterfactual evidence:
Recommended path:
Commands:
Context savings / tradeoffs:
Evidence policy:
Security and permission notes:
Files to inspect:
Validation commands:
Rollback:
Open user decision:
```
