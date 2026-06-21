# Setup

## Purpose

This is the canonical bootstrap and operator guide for Library Ops. Use it for
local setup, common maintenance commands, and evaluator handoff. Deep rationale
lives in `docs/ARCHITECTURE.md`; docs-local decisioning guidance lives in
`docs/AGENTS.md`; validation policy lives in `docs/process/quality-gates.md`.

## 1. First-time bootstrap

```bash
npm ci
uv sync --all-groups
uvx --from code-review-graph code-review-graph --version
uvx --from semgrep semgrep --version
uv tool install -p 3.13 serena-agent
codex doctor --summary --ascii --no-color
npm run checks:precommit
npm run taskmaster:validate
```

## 2. Start Codex

```bash
cd <repo-root>
./scripts/codex-coordinator.sh
codex mcp list
```

Use a shell with the repo environment already loaded. Do not print `.envrc` or
route normal startup through `direnv exec`.

## 3. Task Master runtime

```bash
cp .taskmaster/config.example.json .taskmaster/config.json
npx --yes --package task-master-ai@0.43.1 -c 'task-master models --setup'
```

Keep `.taskmaster/config.json` and `.taskmaster/state.json` untracked.

## 4. Code-intelligence and noisy-output tools

```bash
rtk init -g --codex
uvx --from code-review-graph code-review-graph build
uvx --from code-review-graph code-review-graph status
serena project health-check
npm run astgrep:scan
repomix --config repomix.config.json
```

Use RTK for noisy exploratory output, but preserve raw command output for
security, release, dependency, and final evidence.

## 5. Common eval and research commands

### Deterministic Promptfoo lane

```bash
npm run eval:validate
npm run eval:smoke
npm run eval:ci
```

### Local provider lane

```bash
OLLAMA_BASE_URL=http://127.0.0.1:11434 \
  npx --yes promptfoo@0.121.15 eval -j 1 \
  -c evals/release/control-plane-provider.yaml \
  --no-cache --output reports/validation/promptfoo-provider-local.json
```

Verify the local provider before trusting it:

```bash
ollama --version
ollama ps
curl -sS http://127.0.0.1:11434/api/generate -d '{"model":"qwen3.5:0.8b","prompt":"Return JSON only: {\"ok\":true}","stream":false}'
```

### Review-graph lane

```bash
npm run graph:build
npm run graph:status
npm run graph:review
```

### Direct structured search

```bash
npm run astgrep:scan
```

## 6. Branch setup

```bash
git checkout main
git push -u origin main
git checkout -b development
git push -u origin development
```

Feature work should branch from `development`.

## 7. Handoff artifacts

- The current Task Master task/subtask and its notes are the checkpoint
  surface.
- Record command, blocker, and validation evidence in Task Master notes.
- Promote durable lessons into repo docs or skills instead of adding a new
  scratch handoff file.

## 8. Canonical references

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/AGENTS.md`
- `docs/README.md`
- `docs/design/wireframes.md`
- `docs/evaluation/eval-strategy.md`
- `docs/process/quality-gates.md`
- `docs/process/sdlc.md`
- `.taskmaster/docs/prd.md`
- `AGENTS.md`

## 9. Notes

- Required local tools are blockers, not shortcuts.
- Do not commit provider keys, OAuth state, generated corpora, embeddings,
  local databases, or other transient outputs.
