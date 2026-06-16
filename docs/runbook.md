# Runbook

## Purpose

This is the short operational flow for working in the repo after bootstrap.
Keep machine-specific runtime policy in `.taskmaster/`, not here.

## 1. Verify the local control plane

```bash
npm run checks:precommit
codex doctor --summary --ascii --no-color
npm run taskmaster:validate
npm run verify:core
```

Use `npm run checks:precommit` for the fastest local hygiene loop, `npm run
verify:core` for the comprehensive local loop, and `npm run verify:all` when
you want the same loop plus the full security aggregate.

## 2. Verify Codex and MCP state

```bash
codex mcp list
```

If a provider or OAuth login is missing, repair it with the documented
`codex mcp add ...` or `codex mcp login ...` command and record that exact step
in the current task notes.

## 3. Verify code-intelligence tools

```bash
rtk init -g --codex
uvx --from code-review-graph code-review-graph status
serena project health-check
ast-grep scan
repomix --config repomix.config.json
```

Use RTK for noisy exploratory output, but preserve raw output for security,
release, dependency, and final evidence.

## 4. Generate or inspect the Task Master graph

Use the canonical Task Master workspace docs:

- `.taskmaster/README.md`
- `.taskmaster/docs/runtime-policy.md`

After generation or provider changes, reconcile the graph against:

- `.taskmaster/docs/prd.md`
- `specs/001-core/tasks.md`
- `docs/adr/index.md`
- `docs/architecture/architecture-approach.md`

## 5. Hook sanity checks

```bash
uv run --project "$(git rev-parse --show-toplevel)" python "$(git rev-parse --show-toplevel)/.codex/hooks/serena_hook.py" cleanup
printf '{"session_id":"test","transcript_path":"/tmp/nonexistent","cwd":"<repo-root>"}' | uv run --project "$(git rev-parse --show-toplevel)" python "$(git rev-parse --show-toplevel)/.codex/hooks/serena_hook.py" cleanup
```

The first command should exit cleanly with a skip message. The second should
also exit cleanly without a traceback.

## 6. Security and release checks

```bash
npm run security:scan
npm run release:check
npm run skills:audit
```

## 7. Troubleshooting rules

- Missing required tools are environment blockers, not optional shortcuts.
- Do not copy provider keys or OAuth tokens into tracked files or derived
  reports.
- If a hook fails, identify which sub-hook failed instead of writing “the hook
  failed” generically.
- If generated tasks or docs drift from the PRD or ADRs, update the higher
  source-of-truth layer first and then regenerate or reconcile the lower layer.

## Canonical references

- `.taskmaster/docs/runtime-policy.md`
- `docs/process/quality-gates.md`
- `docs/process/sdlc.md`
- `docs/how-to/run-promptfoo-suites.md`
- `docs/how-to/onboard-serena.md`
