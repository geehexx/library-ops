# Control-plane tests

This directory validates the executable and machine-readable Codex control
plane. It deliberately avoids testing English sentences as an API.

## Owned here

- `.codex/config.toml` parsing and relative custom-agent path resolution.
- Custom-agent identity, required fields, permission-profile references, and
  orphan detection.
- MCP transport coherence, required/enabled posture, tool lists, and timeouts.
- `.codex/hooks.json` structure, approved event surface, bounded commands,
  worktree-rooted script paths, and referenced hook files.
- Hook input/output behavior for `SessionStart` and `Stop`.
- Skill identity and explicit reference linkage where progressive disclosure
  depends on it.
- ADR index parity and hidden bidirectional-control detection.
- Local `package.json` script references and Promptfoo runtime wrapping.

## Owned elsewhere

- Prompt wording and policy semantics: `promptfooconfig.yaml` and `evals/`.
- Django/product behavior: unit, integration, property, smoke, and E2E tests.
- Python architectural boundaries: import-linter and ast-grep rules.
- Tool installation and live MCP connectivity: implementation/release
  preflight commands.
- GitHub helper implementation tests: `tests/tooling/`.

## Commands

Fast standalone contract check:

```bash
python scripts/check_control_plane.py
python scripts/check_control_plane.py --json
```

Executable tests:

```bash
uv run pytest tests/control_plane -q
```

A deliberate policy change starts in `contract.toml`, not in another exact
prose assertion.
