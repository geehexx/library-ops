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

### Full local loop

```bash
npm run verify:all
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
- Ruff, Pyright, pytest, Import Linter, and Django checks
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
