# Onboard Serena without repeated manual activation

Serena is a required local semantic-code MCP for implementation work. It must be available before broad source edits, symbol moves, multi-file refactors, or dependency-impact claims.

## Policy

- Serena is operator-local tooling; `.serena/` and `.serena-memory/` stay ignored.
- The project MCP starts Serena with `--project-from-cwd --context=codex` so the active repository is inferred from the Codex working directory.
- Session start hooks may run `serena_hook.py activate` once per Codex startup or
  resume to establish trusted project context. That hook is expected and is not
  the same as repeated manual activation churn.
- Ongoing proof of health should come from MCP startup plus
  `serena project health-check` evidence.
- Stop hooks may still run cleanup and session summary reminders.

## Install and initialize

```bash
uv tool install -p 3.13 serena-agent
serena init
serena project health-check
```

## Codex MCP startup contract

The project config must keep:

```toml
[mcp_servers.serena]
command = "serena"
args = ["start-mcp-server", "--project-from-cwd", "--context=codex"]
required = true
```

## Required evidence

Run:

```bash
serena --version
serena project health-check
```

Record the exact output or blocker in the current task notes or local evidence
bundle before implementation work.

The current repo-local check on 2026-06-16 completed successfully with
`✅ Health check passed - All tools working correctly`.

## Use rule

Before broad source changes, record which Serena retrieval, navigation, or refactor path was used or why it was not available. Pair Serena with code-review-graph, ast-grep, direct source reads, and tests.
