---
name: promptfoo-evals
description: Use when authoring, expanding, validating, running, or triaging Promptfoo eval suites, deterministic assertions, provider-backed semantic tests, red-team plans, or agent/control-plane prompt regression coverage.
---

# Promptfoo Evals

## Purpose

Use this skill to turn Library Ops control-plane and product-agent behavior into repeatable Promptfoo suites.

Read `references/lane-guide.md` for the lane breakdown, assertion preferences, and
reporting conventions that accompany this skill.

When evaluation work needs live browser automation or reproducible UI-flow
debugging outside Playwright test files, use the installed `$playwright` skill
alongside this one.

## Procedure

1. Find existing Promptfoo config, prompts, tests, and result notes.
2. Map the behavior under test to one of the repo lanes: config, deterministic smoke, provider-backed semantic, red-team, or release regression.
3. Prefer deterministic assertions such as `contains`, `not-contains`, `is-json`, `javascript`, or `python` before model-graded rubrics.
4. Use Promptfoo Nunjucks environment syntax such as `{{env.OPENAI_API_KEY}}`; do not use shell `$OPENAI_API_KEY` syntax inside YAML.
5. Keep reusable prompts and larger test cases in files under `evals/`, then reference them from config.
6. Validate every config before running it.
7. Record command, provider, model, exit code, and result location in the validation transcript or dogfooding report.

## Deterministic control-plane smoke

```bash
npm run eval:validate
npm run eval:smoke
```

Use this lane for source-of-truth wording, artifact taxonomy, no-secret policies, Task Master local-only config, and Codex auth handling.

## Provider-backed semantic lane

Use this lane only when a local provider has been approved and configured. Keep provider secrets in local environment or user-level tool config.

```bash
OLLAMA_BASE_URL=http://127.0.0.1:11434 npx --yes promptfoo@0.121.15 eval -j 1 -c evals/release/<suite>.yaml --no-cache --output reports/validation/promptfoo-<suite>.json
```

For the current Library Ops local-provider lane, the validated shape is:

- `ollama:chat:qwen3.5:0.8b`
- serial execution with `-j 1`
- explicit `OLLAMA_BASE_URL=http://127.0.0.1:11434`

## Red-team lane

Map the app boundary first. Do not run a broad red-team scan until the target, inputs, auth posture, and unsafe-action policy are explicit.

```bash
npx --yes promptfoo@0.121.15 redteam init
npx --yes promptfoo@0.121.15 redteam run --tag git.sha="$(git rev-parse HEAD)"
npx --yes promptfoo@0.121.15 redteam report
```

## Result block

```text
Promptfoo result
Lane:
Config:
Provider/model:
Command:
Exit code:
Assertions added/changed:
Failures:
Security implications:
Next rerun:
```
