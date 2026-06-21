# Changelog

This file is managed by Python Semantic Release.

## [Unreleased]

### Changed

- Reconciled the live Django bootstrap with the planning surfaces so Task Master,
  the PRD, and README no longer describe a second nested `django-admin
  startproject` pass.
- Hardened the Django settings baseline with `DATABASE_URL` parsing, explicit
  Django test-host handling, and test settings that respect Postgres when CI
  provides it.
- Tightened CI, policy, and dependency automation parity by switching
  Dependabot Python updates to `uv`, allowing `deps` commit prefixes, adding
  Bandit to the documented security aggregate, and enforcing workflow-policy
  checks in CI.
- Fixed the GitHub review helper scripts so pending check JSON is parsed,
  exhausted pagination does not duplicate records, and PR comment collection
  targets the base repository context instead of the fork head.
- Reworked skill-reference taxonomy toward concrete names and added governance
  tests for skill references, ADR index alignment, and bidi-control safety.
- Promoted a proven local-first Task Master lane based on bounded Ollama runs,
  committed phase PRDs for local-model-friendly regeneration, and aligned the
  runtime policy, Task Master config example, and task graph notes around that
  evidence.
- Removed unproven Spark-specific agent lanes and demoted private design-tool
  workflows so repo-local wireframes remain the only committed design authority.
- Fixed remaining control-plane release and automation defects by adding an
  explicit Python build backend, sanitizing Task Master subtask parent IDs,
  making Semgrep path filters future-proof, and running Codex hook scripts with
  `uv run --no-sync`.
- Reconciled release-convergence planning truth so the PRD, continuation
  surfaces, and Task Master status no longer describe the implemented Django
  product surfaces as merely planned or bootstrap-only.

### Remaining Release-Convergence Work

- External Google/GitHub social-auth proof on local plus Render remains blocked
  on provider-console and hosted-environment state outside the repo.
- Remaining in-repo merge/governance work is limited to explicit post-merge
  cleanup and milestone-board follow-through; the screenshot matrix route
  inventory is already closed, and the only remaining evaluator-visible blocker
  is external social-auth proof under `16.6`.
