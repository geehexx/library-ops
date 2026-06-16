---
id: DOC-CONTEXT-TOOLING-STRATEGY
title: Codex Context, MCP, and Required Tooling Strategy
status: active
last_reviewed: 2026-06-13
related_adrs:
  - ../adr/0004-agent-toolchain-mcp-and-context-optimization.md
  - ../adr/0007-agent-skills-and-meta-system-governance.md
---

# Codex Context, MCP, and Required Tooling Strategy

## Operating decision

The implementation environment must provide the selected local stack. Missing
tools are environment defects and should be reported with direct command
evidence, not explained away with wrapper prose.

Authoritative detail lives in:

- `AGENTS.md`
- `.codex/config.toml`
- `.codex/agents/*.toml`
- `.agents/skills/*/SKILL.md`
- ADR-0004 and ADR-0007

This file is the compact summary, not a second operating manual.

## Context acquisition order

1. Read the current Task Master task and the linked PRD section.
2. Read the relevant constitution principle, ADR, and skill.
3. Run or inspect `git status`.
4. Use code-review-graph for graph/blast-radius questions.
5. Use Serena for symbol-level project understanding.
6. Use ast-grep for syntax-aware checks that would be brittle with regex.
7. When shell inspection is still needed, batch related `rg`, `sed`, and `find`
   calls rather than making many one-file reads.
8. Use direct file inspection before editing.
9. Use Repomix only when the task genuinely needs a bounded multi-file context pack.
10. Use Context7 for current library/API docs and Exa for broader current research.
11. Use RTK for noisy shell output; preserve raw output when evidence-sensitive.

## Model and orchestration summary

- Root default: `gpt-5.4`
- Read-heavy planning/research specialists: `gpt-5.4-mini`
- Spark micro-workers: `gpt-5.3-codex-spark` when explicitly invoked
- Fan-out cap: `agents.max_depth = 1`, `agents.max_threads = 8`
- Root stays the only interactive coordinator
- Specialists are called directly by the root unless a later validator-backed
  experiment re-enables recursion

Recursive fan-out is not the active default. `agents.max_depth = 1` keeps the
control plane aligned with the current proven workflow and with current Codex
guidance. ADR-0008 owns the guardrails for any future experiment that raises
that cap again. Read-heavy planning and research stays on `gpt-5.4-mini`.
Spark-named agents may still be useful for bounded text-only summaries or
community-source cleanup, but raw commands remain authoritative for final
validation evidence.

Goal budgeting is separate. For long-horizon `/goal` work, omit goal token
budgets by default and use measurable completion criteria instead.

## MCP configuration posture

Project MCPs are declared in `.codex/config.toml`:

```text
required: context7, exa, taskmaster-ai, code-review-graph, serena
task-scoped optional: figma
```

Codex supports project-scoped `.codex/config.toml`, STDIO servers, Streamable
HTTP servers, bearer-token/OAuth auth, `required`, `enabled_tools`, and tool
approval controls. This project uses those controls to keep the selected
toolchain visible to agents and to restrict the graph MCP to approved
review/graph tools.

Figma is configured for design tasks but is not a global startup blocker because
OAuth state is operator-local and may not propagate to subagents or new sessions.
If a Figma-backed design task needs the connector and auth is missing, the agent
must ask the user to run `codex mcp login figma` in the active environment and
wait for confirmation.

The project `workspace` permission profile is the single filesystem policy
source. It grants repo and temp writes, denies repo-owned environment,
credential, secret, and Task Master runtime-state paths, and lets cache-heavy or
network-heavy commands request explicit approval when they need to write outside
the workspace. Do not mirror those rules in `sandbox_workspace_write` or
specialist permission extensions. Keep broad root `.env.*` denies, and name
committed environment templates `env.example` so they remain normal tracked
files without permission exceptions. Do not use broad workspace globs
such as `**/.env` or `**/*credential*`; generated dependency trees can contain
files with those names and package managers must be able to delete and recreate
them. If local paths are read-only, restart Codex from the trusted repo root or
use the approval flow for the affected command before running gates. Do not use
`:danger-no-sandbox`; use the repository `workspace` profile, or only for an
isolated throwaway run use the documented `--sandbox danger-full-access`. Do not
read or print environment or credential files.

MCP trust rules:

- local STDIO MCPs are local processes and inherit local trust implications;
- remote MCPs introduce account, network, OAuth/token, and prompt-injection boundaries;
- provider/OAuth logins are local state; do not work around missing auth by
  copying tokens into tracked files or generated derived reports or local export bundles;
- new remote/cloud code stores, paid tools, or credentialed integrations still require a user decision;
- prompt/tool-poisoning risk is handled by source review, tool allowlists, approval prompts, and raw evidence requirements;
- MCP output is never the sole release or security evidence.

## RTK policy

Use RTK for noisy first-pass shell commands:

```bash
rtk git status
rtk uv run pytest
rtk uv run ruff check .
rtk npm run markdownlint
```

Use raw commands or full logs for failing tests, ambiguous stack traces,
security/dependency scanner findings, release/deployment proof, and exact
output that will be cited in a PR or task note.

Codex does not get transparent RTK command mutation through a native hook. In
this repo, the savings path is:

- better default scripts such as `checks:precommit`
- explicit `rtk ...` command use when exploration is noisy
- agent instructions that steer noisy work to RTK and exact gates to raw output

## Graph and symbolic tooling

- `code-review-graph` answers blast radius, changed-code context, and structural
  adjacency.
- Serena answers symbol-level retrieval and refactor planning.
- `ast-grep` covers deterministic syntax-aware search or codemod checks.
- Repomix is only for bounded repo packs when graph/symbol search is
  insufficient.

None of these replace source inspection or tests.

## Serena reminder

Codex hooks activate, remind, and clean up Serena context. The repo-owned
PreToolUse reminder only warns after repeated grep/read shell bursts and resets
on symbolic Serena use. Treat the warning as a nudge back toward symbolic or
graph tooling, not as proof that shell inspection is forbidden.

## Spec Kit and alternatives

- Spec Kit is required for planning/governance consistency, but `uvx` is enough;
  it does not need to be a persistent global dependency.
- `ast-grep` stays CLI-first; the MCP path is still unnecessary here.
- Hosted code intelligence, hosted dashboards, and broader context layers remain
  explicit future benchmarks, not default dependencies.

## Required verification commands

```bash
codex doctor --summary --ascii --no-color
npx --yes --package task-master-ai@0.43.1 -c 'task-master validate-dependencies'
npm run checks:precommit
npm run verify:core
```
