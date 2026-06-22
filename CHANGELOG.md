# Changelog

This file is managed by Python Semantic Release.

## [Unreleased]

### Changed

- Refined the live demo and release-review surfaces around the real hosted
  state: search-first catalog UI, truthful auth/demo copy, direct social-login
  provider flow, and a seeded Render verifier that checks home, login, search,
  and librarian/member/admin paths end to end.
- Expanded the demo data model from the tiny bootstrap snapshot to a medium
  seeded corpus with deterministic extra borrowers, richer public-domain import
  slices, and multi-year circulation history while keeping the visible dashboard
  flow readable.
- Added a repeatable hosted verification helper plus docs/runbook updates for
  the manual Render free-tier refresh path.
- Restored the real GitHub-hosted `ci` and `commitlint` workflows so the draft
  `development` -> `main` release PR can regain truthful remote gate
  authority before final promotion.
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

- Rerun the real GitHub-hosted CI and PR gate workflows on release PR `#29`
  and fix any final remote-only failures against the true release candidate.
- Reconcile README, Task Master, and release-status wording to the live GitHub
  and Render state after the real remote gates rerun.
- Run one final seeded hosted evaluator walkthrough, merge `development` into
  `main`, and then finish the post-merge cleanup lane.
