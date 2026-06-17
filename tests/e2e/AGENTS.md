# E2E Tests Rules

- Follow `tests/AGENTS.md` first.
- This subtree owns evaluator-visible browser flows only.
- Use pytest-playwright fixtures instead of manual browser lifecycle code.
- Keep live-server session bridging in `tests/e2e/conftest.py`.
- Prefer semantic locators, role-based navigation checks, and web-first
  assertions.
- When a flow is used for release proof, keep traces and screenshots under
  `output/playwright/` and leave them untracked.
- Treat live-deploy validation as separate from evaluator-visible UI coverage;
  if the service is still blocked, record the blocker in Task Master rather
  than encoding a workaround in the test flow.
- If a flow needs data setup, use factories or explicit seed commands, not
  ad hoc object creation scattered across test bodies.
