# E2E Tests Rules

- Follow `tests/AGENTS.md` first.
- This subtree owns evaluator-visible browser flows only.
- Use pytest-playwright fixtures instead of manual browser lifecycle code.
- Keep live-server session bridging in `tests/e2e/conftest.py`.
- Prefer semantic locators, role-based navigation checks, and web-first
  assertions.
- If a flow needs data setup, use factories or explicit seed commands, not
  ad hoc object creation scattered across test bodies.
