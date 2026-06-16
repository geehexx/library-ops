# Toolchain matrix

The selected implementation environment treats the configured tools as required. A sandbox report may identify missing binaries, but does not make them project-optional.

| Tool | Required role |
|---|---|
| Codex CLI | Main implementation agent and MCP host. |
| Task Master | Derived execution graph, via pinned external CLI/MCP invocation and local-only runtime config. |
| Spec Kit | Spec backbone and consistency, typically checked with `uvx` and initialized only when needed. |
| RTK | Noisy shell-output compression. |
| Serena | Symbol-aware retrieval/refactor planning, kept as a persistent local install because hooks depend on `serena-hooks`. |
| code-review-graph | Graph/blast-radius review, with repo-preferred `uvx` or npm wrapper invocation. |
| ast-grep | Deterministic AST rules/codemods. |
| Repomix | Bounded repo snapshots. |
| Context7/Exa MCP | Docs and research context. |
| Promptfoo | Eval and red-team gate, invoked as a pinned external CLI. |
| Vale/cspell/lychee/alex | Documentation quality. |
| Import Linter/Ruff/Pyright/pytest/Hypothesis/Playwright/Schemathesis/mutmut | Code and behavior quality, primarily through `uv run`. |
| Gitleaks/Semgrep/Bandit/pip-audit/npm audit/actionlint/zizmor/Conftest/CycloneDX | Security, workflow, policy, and supply chain; `semgrep` now prefers `uvx` for local repo runs. |
