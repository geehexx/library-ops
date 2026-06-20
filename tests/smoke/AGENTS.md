# Smoke Tests Rules

- Follow `tests/AGENTS.md` first.
- Smoke tests must stay deterministic, fast, and environment-focused.
- This subtree owns bootstrap, settings, and production-settings verification.
- Avoid turning smoke tests into broad integration suites.
- When a smoke test needs complex setup, move that behavior into integration or
  property coverage instead.
