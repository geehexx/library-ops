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

### Render demo refresh

Render free-tier deploys do not run a seed hook during build, so the live demo
state must be refreshed manually after a deploy or database reset. Set
`LIBRARYOPS_DEMO_ACCESS_CODE` in the Render service environment or the shell
session first, then run:

```bash
uv run python manage.py seed_roles
uv run python manage.py seed_demo_users --reset-passwords
uv run python manage.py import_public_domain_catalog --source openlibrary --limit 5 --refresh
uv run python manage.py import_public_domain_catalog --source gutenberg --limit 5 --refresh
uv run python manage.py seed_circulation_examples --refresh
```

This sequence is idempotent and can be rerun safely to restore the seeded demo
accounts, a medium-sized catalog slice, and deterministic circulation examples
without hardcoding secrets.

### Hosted demo verification

Use the hosted verification helper to capture pass/fail evidence before calling
the live host demo-ready.

Current truthful-state probe:

```bash
uv run python scripts/check_hosted_demo.py --base-url https://library-ops.onrender.com --mode unseeded
```

If the host is still unseeded but OAuth provider links are expected to be live:

```bash
uv run python scripts/check_hosted_demo.py \
  --base-url https://library-ops.onrender.com \
  --mode unseeded \
  --auth-mode provider-enabled \
  --expect-provider google \
  --expect-provider github
```

Post-refresh seeded proof:

```bash
LIBRARYOPS_DEMO_ACCESS_CODE='<demo access code>' \
  uv run python scripts/check_hosted_demo.py \
  --base-url https://library-ops.onrender.com \
  --mode seeded \
  --auth-mode provider-enabled \
  --expect-provider google \
  --expect-provider github \
  --report-file reports/validation/hosted-demo-seeded.json
```

This helper proves the public home/login/catalog surfaces and, when the demo
password is available, the seeded librarian/member/admin flows too. It does not
replace browser-backed OAuth callback proof for Task `16.6`; use it to tighten
the seeded-host evidence before or alongside the browser run.

Add `--expect-provider google --expect-provider github` once the hosted login
page is supposed to expose live provider links.

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
