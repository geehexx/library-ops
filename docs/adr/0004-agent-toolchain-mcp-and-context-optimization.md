# ADR-0004: Agent toolchain, MCP, and context optimization

- Status: accepted selected stack; open only for remote/paid/credentialed expansion
- Date: 2026-06-13
- Deciders: Andrew Crozier

## Context

The user explicitly wants RTK deeply integrated and wants code-review-graph plus current MCP/tool alternatives reviewed and integrated rather than treated as vague optional enhancements. The project targets Codex CLI with a 500,000-token coordinator-root context, specialist agents, skills, hooks, MCPs, and strict quality gates. Large context does not remove the need for context quality, tool discipline, or raw evidence.

## Decision

The selected implementation-environment stack is required:

| Layer | Required selection | Role |
|---|---|---|
| Agent harness | Codex CLI/App project config | Primary implementation surface. |
| Docs/research MCP | Context7 and Exa | Current API docs, web research, examples, and counterfactual evidence. |
| Task execution MCP/tool | taskmaster-ai / task-master | PRD parsing, task graph, complexity analysis, execution notes. |
| Shell-output optimization | RTK | Compress noisy shell output before it enters context. |
| Structural graph | code-review-graph | Local graph, blast-radius, review context, dependency map. |
| Symbolic code intelligence | Serena | Symbol-aware retrieval/refactor planning via MCP. |
| Deterministic AST search | ast-grep CLI | Syntax-aware search, lint, and codemod candidates. |
| Bounded repo packs | Repomix | Token-counted snapshots when graph/symbol/AST queries are insufficient. |
| Skill validation | custom validator plus agent-skills-lint when available | Validate Codex skill schema, collisions, and skill context quality. |
| Security/quality | Gitleaks, Semgrep, pip-audit, npm audit, actionlint, zizmor, Conftest | Left-shift gates for secrets, SAST, dependency risk, workflow risk, and policy. |

The project config declares Context7, Exa, Task Master, code-review-graph, and Serena MCP servers. Context7, Exa, Task Master, code-review-graph, and Serena are startup-required in implementation environments. ast-grep remains a required CLI rather than a default MCP because the official MCP server is experimental and duplicates safer deterministic CLI usage. Remote/cloud code-indexing and paid services are deferred until the user approves credentials, code-export boundaries, cost, and retention.

RTK may filter noisy command output, but final evidence requires raw output/full logs for ambiguous failures, security results, release evidence, and exact diagnostics.
Provider and OAuth setup must use official local commands such as
`task-master models --setup`; agents must stop and
ask the user to run those commands when interactive login is required.

## Alternatives considered

| Alternative | Benefit | Rejected or adapted because |
|---|---|---|
| Raw commands only | Maximum fidelity | Wastes context and worsens long-running agent sessions. |
| RTK only | Strong shell-output savings | Does not solve symbol retrieval, graph blast radius, or AST codemods. |
| code-review-graph only | Strong structural map | Graph output is not proof and does not replace symbol-aware refactor tools. |
| Serena only | Strong symbol workflow | LSP/symbol scope does not replace graph/risk or deterministic AST search. |
| ast-grep MCP | Agent-native AST tooling | Current server is experimental; CLI is narrower and easier to audit. |
| Repomix always | Simple whole-repo context | Too broad; can leak noise/secrets without tight excludes and token budgets. |
| tokenix / Headroom / LeanCTX | Broader context layers | Promising but broader interception needs more local benchmarking before being selected. |
| Cloud semantic-code stores | Powerful retrieval | Code-export, retention, credentials, and cost require explicit user approval. |
| No MCPs | Smaller attack surface | Loses current docs, task orchestration, graph, design, and symbol workflows. |

## Consequences

- The selected local toolchain is not “optional” in real implementation environments.
- A constrained sandbox may validate configuration and report missing binaries, but should not normalize skipping required tools or downgrading proof claims. When a workflow such as headed Playwright needs broader browser/process access than the default workspace-write sandbox allows, the session should explicitly switch to the required access mode rather than claiming partial proof from a blocked lane.
- Agent instructions should route broad tools to the roles that own the work.
- The agent catalog includes dedicated Spark lanes for read-only debugging and
  one-file quick fixes; the general implementer lane stays for broader bounded
  slices.
- MCP trust is explicit: stdio MCPs run local processes with user permissions; remote MCPs require token and data-flow review.

## Validation

- `.codex/config.toml` declares the selected MCPs, the coordinator-root permission profile, and the committed 500,000-token root context contract.
- `codex --profile <name>` overlays are user-local files under `~/.codex/<name>.config.toml`; they are operator state, not repo-owned config.
- `codex doctor`, `npx --yes --package task-master-ai@0.43.1 -c 'task-master validate-dependencies'`, and direct tool probes report/fail on missing runtime or tooling prerequisites.
- The remaining repo checks should stay thin and favor direct tool invocation over custom verifier wrappers.
- `.code-review-graphignore`, `repomix.config.json`, `sgconfig.yml`, `.gitleaks.toml`, `.semgrep.yml`, and policy files define tool behavior.
