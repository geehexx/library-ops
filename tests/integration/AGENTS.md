# Integration Tests Rules

- Follow `tests/AGENTS.md` first.
- This subtree owns DB-backed orchestration, management commands, and
  permission-sensitive Django view flows.
- Keep modules kind-first under `tests/integration/<domain>/`.
- If a slice becomes browser-driven, move it to `tests/e2e/`.
