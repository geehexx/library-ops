# Code intelligence tool routing

Use this reference when the coordinator needs exact tool-selection evidence for
Library Ops control-plane work.

## Source order

1. Repo source of truth: `AGENTS.md`, `.specify/memory/constitution.md`,
   `.taskmaster/docs/prd.md`, `specs/001-core/*`, and current Task Master state.
2. Local tool evidence: raw shell output, Serena, code-review-graph, ast-grep,
   RTK, Repomix, and validator results.
3. Primary upstream docs for Codex, Task Master, Figma MCP, Promptfoo, and
   package managers.
4. Exa/web/community sources only for discovery or counter-evidence, with
   confidence labels.

## Tool routing

- Use Serena for symbol-aware code navigation and refactor planning.
- Use code-review-graph for dependency/blast-radius review and test mapping.
- Use ast-grep for syntax-aware searches or codemod candidates.
- Use RTK for noisy exploratory command summaries, then rerun raw commands for
  release evidence.
- Use Repomix only for bounded, redacted repo packs that are not committed.

## Evidence requirements

Every material tooling recommendation should record the command, exit code,
source path or URL, confidence, and whether the output is final evidence or a
lossy summary.
