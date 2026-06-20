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

### Not Yet Implemented

- Product-domain Django apps, models, APIs, and UI flows beyond the current
  bootstrap and smoke-test surface remain pending.
