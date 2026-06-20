---
id: DOC-QUALITY-GATES
title: Quality Gates and Left-Shift Validation
status: active
last_reviewed: 2026-06-16
related_prd: ../../.taskmaster/docs/prd.md
related_adrs:
  - ../adr/0005-delivery-quality-security-and-release.md
  - ../adr/0007-agent-skills-and-meta-system-governance.md
---

# Quality Gates and Left-Shift Validation

## Principle

A gate is useful only when it fails in an unambiguous way, has a remediation path, and leaves
evidence that can be copied into Task Master notes or a PR.

## Primary gate ladders

### Fast local hygiene loop

```bash
npm run checks:precommit
```

### Control-plane loop

```bash
codex doctor --summary --ascii --no-color
npm run taskmaster:validate
npm run verify:core
```

### Control-plane bootstrap loop

Run this before broad implementation when agent/config/hook surfaces changed:

<!-- cspell:disable -->
```bash
python - <<'PY'
import pathlib,tomllib
paths=[pathlib.Path('.codex/config.toml'),*sorted(pathlib.Path('.codex/agents').glob('*.toml'))]
for p in paths:
    tomllib.loads(p.read_text())
    print("OK", p)
PY
codex features list
codex mcp list
codex doctor --summary --ascii --no-color
```
<!-- cspell:enable -->

### Full local loop

```bash
npm run verify:all
```

### Phase 1 validation ladder

```bash
uv run ruff format --check .
uv run ruff check .
npm run python:lint
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
PYTHONPATH=src uv run lint-imports
uv run pyright
uv run pytest tests/smoke tests/web tests/e2e
```

## What the aggregate gates cover

`npm run verify:core` covers:

- skill lint
- strict skill audit
- docs quality
- docstring coverage and docstring lint for repo-owned Python
- deterministic Promptfoo evals
- dependency-tree integrity
- workflow lint
- policy checks
- release readiness
- Ruff, Django `check`, Django `makemigrations --check --dry-run`, Pyright, pytest, and Import Linter
- source complexity and docstring lint (`npm run python:lint`)
- Task Master validation

`npm run verify:all` adds:

- Gitleaks
- Semgrep
- pip-audit
- `npm audit --audit-level=moderate`

## Source-adjacent documentation loop

```bash
npm run docstrings:coverage
npm run docstrings:lint
```

## Tool-specific rules

- Use RTK for noisy exploratory output, not for final security or release proof.
- Use graph/symbol tools for planning, then confirm with source inspection and
  tests.
- Use Context7 first for official API, SDK, and library documentation; fall
  back to Exa or web research for discovery, examples, and counter-evidence.
- When a Django module grows into multiple behavior groups, split it into a
  package and enforce the public surface with `__all__` re-exports plus a
  governance test.
- Preserve raw scanner output for security, supply chain, and release evidence.
- Keep Task Master runtime/provider policy in `.taskmaster/docs/runtime-policy.md`.

## PR evidence minimum

Every non-trivial PR should state:

- Task Master ID
- PRD sections
- ADR/docs touched
- required tools used
- checks run
- known gaps
- rollback path

## Failure rule

When a gate fails:

1. stop broad implementation
2. preserve the raw output
3. classify the failure narrowly
4. fix the smallest real cause
5. update Task Master notes with result and follow-up
