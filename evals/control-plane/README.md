# Control-plane Promptfoo evals

This directory contains deterministic control-plane eval material. The current smoke suite deliberately uses the `echo` provider so it can run in CI and in constrained environments without provider credentials.

## Current coverage

- source-of-truth order
- Question and Escalation packets
- canonical / derived / operator-local artifact taxonomy
- Task Master local-only config posture
- Codex/Figma OAuth posture
- direct-tool verification expectations
- no committed secrets, token files, or unverified generated task claims

## Expansion path

1. Keep deterministic smoke assertions in `promptfooconfig.yaml` while the suite is compact.
2. Move larger case sets to `evals/control-plane/*.yaml` and reference them with `file://` when the suite grows.
3. Add provider-backed release suites under `evals/release/` only after local provider setup succeeds. The dormant template at `evals/release/control-plane-provider.template.yaml` records the intended shape without requiring credentials in CI.
4. Add red-team configs after the app boundary and auth model are implemented.

## Examples

See `docs/evaluation/promptfoo-examples.md` for deterministic, provider-backed, and red-team template examples.
