# ADR-0005: Delivery, quality, security, and release governance

- Status: accepted
- Date: 2026-06-13
- Deciders: user, project coordinator
- Supersedes: ADR-0007, ADR-0008, ADR-0015

## Context

The repository must demonstrate best-in-class delivery discipline without hiding behind verbose custom code. The project is a showcase, so the quality gates are part of the product evidence.

## Decision

Use GitHub flow with protected `main` and `development`, feature branches, Conventional Commits, semantic-release-compatible history, and layered quality gates.

Required gates:

- Repo hygiene: no junk/generated artifacts, no obvious secrets, branch policy, control-plane package/meta verification.
- Agent/meta: Codex config validation, required tool declaration, skill schema validation, agent/tool instruction linting.
- Python: Ruff format/check, Pyright strict type check, Import Linter, pytest, coverage, Hypothesis property tests.
- Django: `manage.py check`, migration dry-run, service/selector/import-boundary review.
- Browser/accessibility: Playwright E2E and accessibility checks after UI bootstrap.
- Security/supply chain: Gitleaks, Semgrep, pip-audit, npm audit, Dependabot, CodeQL/Scorecard where appropriate.
- GitHub Actions: actionlint and zizmor.
- Policy-as-code: Conftest/OPA rules for Codex config, workflow permissions, and repository governance.

Render is the primary documented deployment path, with portability to other Python/PostgreSQL-friendly deployment platforms. Deployment details are operational runbook content, not separate architecture decisions unless the platform choice changes.

Workflow-security posture, updated 2026-06-15: pin the GitHub Actions used by
the repo workflows to concrete commit SHAs and keep `zizmor` clean without a
local exception file. Branch protection must require `quality`,
`workflow-security`, `security`, `policy`, and `commitlint`.

Release workflow posture, accepted 2026-06-14: the current release workflow is a
read-only readiness check that verifies changelog and version generation
without committing, tagging, pushing, or creating a remote release. It must not
mask failures with `|| true`, and it must not hold write or OIDC permissions
until a real publishing flow is explicitly approved.

Task Master packaging posture, updated 2026-06-16:

- The repo no longer vendors `task-master-ai` in its own npm dependency graph.
- Task Master now runs as a pinned external CLI and MCP package at
  `task-master-ai@0.43.1`.
- This keeps the repo-owned npm audit surface clean while preserving Task Master
  CLI and MCP behavior.
- If Task Master is re-vendored later, rerun `npm ci`, `npm ls`,
  `npm audit --audit-level=moderate`, Task Master CLI smoke, and Task Master
  MCP smoke before treating the change as acceptable.

## Alternatives considered

| Alternative | Benefit | Rejected or adapted because |
|---|---|---|
| Minimal CI only | Faster early iteration | Not suitable for an interview showcase centered on disciplined delivery. |
| Custom validators only | Full control | Reimplements mature tools and hides industry familiarity. |
| Third-party scanners only | Fast setup | Cannot validate project-specific agent/meta rules. |
| Trunk-only direct pushes | Simple solo flow | Loses reviewable branch/PR evidence. |
| Vercel-first deployment | Familiar demo path | Django/PostgreSQL/search stack is better served by Render/Fly/Railway-style hosts. |

## Consequences

- Some gates activate only after implementation files exist, but their configuration is present from the start.
- Missing required local tools blocks a real implementation environment unless explicitly waived for sandbox inspection.
- CI and hooks remain optimized for early failure, not just final release.
- If Task Master is ever brought back into the repo-owned npm graph, treat that
  as a fresh supply-chain decision rather than inheriting the previous state.

## Validation

- `.github/workflows/ci.yml`, security workflow, pre-commit hooks, and direct commands encode gates.
- `codex doctor --summary --ascii --no-color` plus direct tool probes fail fast when required local tools are absent or misconfigured.
- Branch protection is documented as a manual/admin setup concern, not a repo helper workflow.
- Branch protection requires quality, workflow-security, security, policy, and
  commitlint checks.
- `npm audit --audit-level=moderate --loglevel=verbose` remains the required
  command for supply-chain evidence.
