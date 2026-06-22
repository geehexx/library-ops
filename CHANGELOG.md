# Changelog

All notable release-level changes to **Library Ops** are documented in this file.

This changelog follows the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
structure and uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
It records what is shipped in each release, not temporary packaging iterations,
transient agent preflight attempts, local repair states, or intermediate
branch history.

## [Unreleased]

Target release: `0.1.1`

### Added

- Added role-selecting local signup and social-signup completion flows that
  normalize every new account to exactly one application role group.
- Added a dedicated lexical-search package structure and a kind-first property
  test topology with reusable strategies and a control-plane topology guard.

### Changed

- Changed the canonical PRD root to `docs/PRD.md` and reduced
  `.taskmaster/docs/prd.md` to a compatibility shim instead of a second source
  of truth.
- Changed the evaluator-facing UX slice so account recovery and signup pages
  use the branded shell, catalog language now prefers "catalog record" over
  "foundation record", dashboard cards and demo guidance are easier to follow,
  and exact-identifier search cards visibly show the matched identifier plus
  live availability.
- Changed the importer/search validation story so the public-domain catalog
  import command and its focused integration suite are fully green under the
  touched-scope checks.
- Changed Task Master runtime guidance to record that the current Ollama-backed
  full-PRD parse path is not sufficient for committed graph replacement.

<!-- version list -->

## [0.1.0] - 2026-06-22

Initial evaluator-ready release of the Library Ops Django application and its
repo-local engineering control plane. This release is intended to show the
working mini library-management product, the implementation evidence behind it,
and the disciplined SDLC artifacts used to build and validate it.

### Added

#### Product application

- Added a Django 5.2 library-management application with a server-rendered UI,
  root dashboard, health endpoint, catalog routes, circulation routes, local
  settings, production settings, ASGI/WSGI entry points, and Render-oriented
  deployment support.
- Added role-aware navigation and application surfaces for the evaluator,
  anonymous visitor, member, librarian, and administrator paths.
- Added password-based demo authentication as the default evaluator path, with
  optional environment-driven OAuth/social-provider configuration.
- Added production settings that fail loudly when required production secrets,
  hosts, or database configuration are missing.

#### Catalog management

- Added a normalized catalog model instead of a single flat book table:
  `BibliographicWork`, `Contributor`, `WorkContributor`, `BookEdition`, and
  `ExternalSourceRecord` now separate conceptual works, contributor identities,
  publication/edition metadata, and import provenance.
- Added catalog management flows for creating, editing, and archiving works,
  editions, and copies through Django forms and templates.
- Added ISBN normalization and validation, including ISBN-10 to ISBN-13
  normalization and checksum validation.
- Added cover metadata support with cover URLs, uploaded cover images, file-size
  validation, decoded image-format validation, and stable upload-path handling.
- Added catalog admin registrations and operational metadata so the domain can
  be inspected and maintained through the Django admin surface.
- Added append-only audit events for protected catalog mutations.

#### Inventory and circulation

- Added `BookCopy` inventory records with unique barcodes, shelf/condition
  metadata, archival state, and explicit copy statuses: available, on loan,
  maintenance, lost, and archived.
- Added a `Loan` model for checkout and return history, with due dates,
  borrower links, checkout actor, return actor, returned timestamp, and active
  loan state.
- Added a database-level active-loan invariant so one copy cannot have more than
  one open loan at the same time.
- Added transactional checkout orchestration that locks the selected copy,
  creates a loan, marks the copy on loan, and records audit metadata.
- Added transactional return orchestration that closes the active loan, restores
  copy availability, and records audit metadata.
- Added circulation dashboard slices for librarians and members, including a
  member-scoped view of the member's own loans.
- Added HTMX-compatible checkout and return workflow fragments for browser
  modal/dialog use while preserving full server-side form handling.

#### Search and discovery

- Added ORM-backed lexical catalog search that works in SQLite-backed tests and
  leaves a clean path for PostgreSQL full-text-search ranking in production.
- Added exact-identifier-first ranking for ISBN, barcode, Open Library, and
  Project Gutenberg identifiers so authoritative catalog identifiers outrank
  broader keyword or phrase matches.
- Added title, contributor, subject, availability, provenance, and keyword search
  filters with stable result explanations.
- Added PostgreSQL-weighted keyword ranking support for deployments that run on
  PostgreSQL.
- Added availability filtering based on live copy and active-loan state rather
  than a manually edited display flag.

#### Seed data and demo corpus

- Added idempotent role seeding for Admin, Librarian, and Member permissions.
- Added demo-user seeding with resettable demo credentials for evaluator runs.
- Added deterministic public-domain catalog import support with provenance,
  dry-run, limit, and refresh behavior.
- Added circulation example seeding so the evaluator can inspect available,
  checked-out, and returned-copy states without hand-building data.

#### Quality, tests, and validation evidence

- Added unit coverage for catalog normalization, forms, admin registration,
  audit boundaries, inventory managers, circulation services, circulation views,
  and lexical search ranking.
- Added integration coverage for role/demo-user seed commands, public-domain
  catalog import, circulation seed examples, catalog management UI, and the
  evaluator-facing foundation UI.
- Added property-based tests for circulation loan invariants and lexical search
  normalization.
- Added Playwright-backed browser coverage for authentication, navigation,
  catalog detail pages, catalog management access control, circulation
  checkout/return flows, exact-identifier search ranking, and visual-regression
  support.
- Added smoke tests for the committed Django bootstrap and Render deployment
  contract.
- Added aggregate validation commands for pre-commit hygiene, documentation
  quality, release readiness, governance checks, security checks, Python checks,
  Promptfoo evals, and Task Master dependency validation.

#### Documentation and architecture

- Added a canonical PRD, Spec Kit supporting artifacts, phase plan, task graph,
  architecture notes, ADRs, process docs, evaluator demo script, quality-gate
  documentation, retrospective workflow, context-lineage reference, and
  question-packet schema.
- Added a source-of-truth model that separates canonical product/governance
  artifacts, generated execution artifacts, and operator-local state.
- Added architectural guidance for C4-style orientation, arc42-style quality and
  risk framing, pragmatic domain modeling, and Django layer ownership.
- Added release and SDLC guidance for development-to-main flow, release PRs,
  release-readiness checks, and Python Semantic Release integration.

#### Agent and control-plane system

- Added repo-local Codex instructions, coordinator-first operating policy,
  specialist subagent definitions, hooks, command rules, MCP configuration, and
  skills for product, documentation, review, search, seed-data, release,
  Playwright, security, Render deployment, retrospective, and control-plane
  maintenance workflows.
- Added governance tests for control-plane metadata surfaces, session-start and
  session-stop hooks, Serena hook behavior, GitHub helper scripts, and committed
  agent/skill surfaces.
- Added Promptfoo control-plane eval fixtures and release-provider eval lanes for
  validating agent behavior as the project evolves.
- Added policy checks for Codex and GitHub Actions configuration.

#### Deployment and release readiness

- Added Render-oriented production deployment support for the current hosted
  Django path.
- Added README evaluator fast-path commands and current release-status guidance.
- Added a release-readiness GitHub Actions workflow that checks changelog and
  version readiness without publishing, tagging, pushing, or creating a remote
  release.
- Added Conventional Commits and commitlint configuration for release-compatible
  commit history.
- Added Python Semantic Release configuration targeting `CHANGELOG.md` and
  `pyproject.toml` version updates.

### Changed

- Standardized the released product direction around the Django/Render path, the
  normalized Work/Edition/Copy/Loan domain model, server-rendered UI flows, and
  deterministic lexical search.
- Established Task Master tasks as derived execution artifacts rather than the
  canonical product source of truth.
- Established the PRD, constitution, Spec Kit artifacts, ADRs, source code,
  tests, and README as the reviewable evidence chain for evaluator-facing
  behavior.
- Scoped AI functionality out of the released product behavior for `0.1.0`; the
  release ships deterministic search and preserves AI-related planning surfaces
  without exposing unreleased AI mutation or availability logic.

### Security

- Added server-side role enforcement for catalog-management and circulation
  workflows, including member denial for protected mutation paths.
- Added Django authentication, permission, and allauth configuration with
  password-based demo auth enabled by default and OAuth/social auth gated by
  environment variables.
- Added production configuration that requires explicit secret, host, and
  database environment variables.
- Added dependency, secret, static-analysis, workflow, and policy-check command
  surfaces, including Gitleaks, Semgrep, pip-audit, actionlint, zizmor, and
  Conftest/OPA integration points.
- Added repository ignore rules and documentation that exclude secrets, local
  database files, OAuth/session state, generated corpora, embeddings, media,
  caches, virtual environments, node modules, and local agent/tool state from
  committed release artifacts.

### Known limitations

- `0.1.0` is an initial `0.x` release; public APIs and operator workflows should
  not be treated as stable until the project reaches `1.0.0`.
- OAuth/social login is optional and environment-driven; the released evaluator
  path is password-based demo authentication.
- AI-assisted metadata and semantic recommendation behavior are not released in
  `0.1.0`; deterministic lexical search is the shipped discovery feature.
- Release readiness is configured, but remote publishing, tagging, and final
  release PR automation remain intentionally gated behind explicit release
  approval.
- Some verification lanes require local tools, provider credentials, browser
  dependencies, or hosted-service access; when unavailable, the repo policy is to
  record the exact blocker rather than mark the gate as passed.
