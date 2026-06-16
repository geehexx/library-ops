# Local and GitHub Setup

## Purpose

Use this page for first-time local bootstrap and GitHub-side branch setup only.
Do not treat it as the full operational runbook.

## Local bootstrap

```bash
uv sync --all-groups
npm ci
uvx --from code-review-graph code-review-graph --version
uvx --from semgrep semgrep --version
uv tool install -p 3.13 serena-agent
codex doctor --summary --ascii --no-color
npm run checks:precommit
npm run taskmaster:validate
```

This confirms the required local stack is present enough to start control-plane
or product work.

## Codex startup

Project MCPs are already declared in `.codex/config.toml`.

```bash
cd <repo-root>
codex --cd <repo-root>
codex mcp list
```

Start Codex from a shell where direnv has already loaded the repo environment.
Do not print `.envrc` and do not use `direnv exec` as the normal startup path.

## MCP repair commands

Only use these when the local Codex install is missing an MCP entry:

```bash
codex mcp add context7 -- node node_modules/@upstash/context7-mcp/dist/index.js --transport stdio
codex mcp add exa --url 'https://mcp.exa.ai/mcp?tools=web_search_exa,web_fetch_exa'
codex mcp add taskmaster-ai -- npx --yes --package task-master-ai@0.43.1 task-master-ai
npx --yes --package task-master-ai@0.43.1 -c 'task-master models --setup'
```

## Code-intelligence bootstrap

```bash
rtk init -g --codex
uvx --from code-review-graph code-review-graph build
uv tool install -p 3.13 serena-agent
serena project health-check
ast-grep scan
repomix --config repomix.config.json
```

`npm ci` already provides the repo-local Node tools such as `ast-grep` and
`repomix`.

## File ownership

- Commit `env.example`, not `.env.example` or secret-bearing `.env*` files.
- Commit `.taskmaster/config.example.json`, not `.taskmaster/config.json`.
- Keep one-session exports, logs, caches, and local OAuth state out of git.

## Branch setup

```bash
git checkout main
git push -u origin main
git checkout -b development
git push -u origin development
```

Feature work should branch from `development`.

## Branch protection

Configure this in GitHub, not through a repo helper script:

- protect `main` and `development`
- require pull requests and conversation resolution
- require `quality`, `workflow-security`, `security`, `policy`, and `commitlint`
- prevent force pushes and branch deletion
- require CODEOWNERS where applicable

## Canonical follow-up docs

- `.taskmaster/README.md`
- `.taskmaster/docs/runtime-policy.md`
- `docs/runbook.md`
- `docs/process/sdlc.md`
