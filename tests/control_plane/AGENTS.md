# Control Plane Tests Rules

- Follow `tests/AGENTS.md` first.
- This subtree owns governance, hook, session, and repo-policy tests.
- Keep tests here read-mostly with narrow filesystem or process fixtures.
- When adding a new repo policy, prefer an automated test or config check here
  over prose in root docs.
- Use this subtree to prevent regressions like app-local tests under `src/`,
  stale AGENTS references, or broken continuation paths.
