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

### Not Yet Implemented

- Product-domain Django apps, models, APIs, and UI flows beyond the current
  bootstrap and smoke-test surface remain pending.
