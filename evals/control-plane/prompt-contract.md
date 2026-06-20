You are preparing a Codex repo-state summary for {{task}}.

Required control-plane contract:
- Source-of-truth order starts with current working tree, constitution, PRD, specs, Task Master derived tasks, AGENTS, skills, docs, then code/tests.
- Question packet
- Escalation packet
- /goal
- validation evidence
- canonical artifacts
- derived artifacts
- operator-local artifacts
- `codex doctor --summary --ascii --no-color`
- `npx --yes --package task-master-ai@0.43.1 -c 'task-master validate-dependencies'`
- `npm run skills:lint`
- Task Master `.taskmaster/config.json` is local-only and must not be committed.
- Generated `.taskmaster/tasks/tasks.json` is a committed derived execution artifact and must be kept aligned with the current direct-tool workflow and validated dependencies.
- Figma remote MCP uses local Codex OAuth login through `codex mcp login figma`; do not copy raw OAuth tokens into project files.
- Promptfoo deterministic smoke, provider-backed semantic evals, and red-team lanes must be explicit.
- Never include `.env`, `.env.*`, `.mcp.json`, provider keys, OAuth tokens, `.taskmaster/config.json`, caches, node_modules, virtualenvs, generated corpora, or previous local export archives.
