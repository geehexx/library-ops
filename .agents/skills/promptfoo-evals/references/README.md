# Promptfoo eval references

Use this reference when expanding Library Ops eval coverage.

## Assertion preference

1. Deterministic assertions: `contains`, `not-contains`, `equals`, `is-json`, `javascript`, `python`.
2. Similarity assertions for fuzzy prose where deterministic checks are too brittle.
3. Model-graded rubrics only when the source material and rubric are both included in the test context.

## Config patterns

- Use `file://` prompts and test files when the suite grows beyond a few small cases.
- Use Nunjucks syntax for environment references: `{{env.OPENAI_API_KEY}}`.
- Keep API keys out of config, logs, and generated packages.
- Add `--tag` values for CI run IDs, git SHAs, and provider/model names.

## Library Ops lanes

- `promptfooconfig.yaml`: deterministic control-plane smoke.
- `evals/control-plane/`: source-of-truth, artifact, agent, and no-secret contracts.
- `evals/release/`: provider-backed semantic release suites after provider setup succeeds.
- `reports/validation/`: local ignored result summaries when a run benefits from filesystem output; do not treat them as committed repo truth.
