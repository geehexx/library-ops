# Library Ops Phase 1 PRD View

Canonical source: `docs/PRD.md`

## Goal

Ship the first product-facing foundation slice on top of the existing Django
bootstrap.

This phase proves the project has real models, seeded roles/users, server-side
authorization, evaluator-visible pages, and app-owned presentation surfaces
before later branches add the full assignment feature set.

## Includes

- finish the remaining bootstrap hardening/proof work from `C1.F2`
- implement the first durable subset of `C2`
- implement the foundation subset of `C3`
- add one evaluator-visible UI slice that proves the foundation is real
- add baseline unit/integration/property/browser coverage for that slice

## Phase 1 implementation brief

### In scope

- Keep the committed bootstrap layout: root `manage.py` and
  `src/libraryops/config/*`.
- Implement:
  - `BibliographicWork`, `Contributor`, and `WorkContributor` in `catalog`
  - `BookEdition` and `ExternalSourceRecord` in `catalog`
  - `BookCopy` in `inventory`
  - `Loan` in `circulation`
  - `AuditEvent` in `audit`
- Keep `BookEdition` in `catalog` and `BookCopy` in `inventory` to match the
  domain boundary notes.
- Add Django auth plus `django-allauth` local account wiring with environment
  driven readiness for future social providers.
- Seed `Admin`, `Librarian`, and `Member` groups plus disposable demo users.
- Add shared server-side authorization helpers used by views.
- Add:
  - role-aware home/dashboard navigation
  - read-only catalog list/detail pages
  - one librarian/admin-only create flow that persists foundation records
  - audit evidence for the protected mutation path
- Add tests for:
  - bootstrap/settings invariants in `tests/smoke`
  - model validation and database constraints in the product test suite
  - role and permission decisions in `tests/web`
  - protected mutation denial for anonymous/member users in `tests/web`
  - one browser smoke flow for login and role-aware navigation in `tests/e2e`

### Out of scope

- full circulation services and renewal flows
- exact/FTS/vector search implementation
- public-domain import commands beyond role/demo-user seeding
- AI suggestion workflows
- deployment/release evidence work, which stays visible in the phase 4 view

## Exit criteria

- `uv run python manage.py check` passes
- `uv run python manage.py makemigrations --check --dry-run` passes
- migrations apply cleanly on a fresh database
- demo roles and disposable demo users can be seeded deterministically
- domain constraints and RBAC checks are covered by tests
- a browser smoke path proves login plus role-aware navigation

## Suggested validation commands

```bash
uv run ruff format --check .
uv run ruff check .
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
PYTHONPATH=src uv run lint-imports
uv run pyright
uv run pytest tests/smoke tests/web tests/e2e
```

## Suggested local regeneration workflow

Review the committed graph first. If phase-1 regeneration is genuinely needed,
run it as a bounded draft/review lane and compare the result against
`.taskmaster/tasks/tasks.json` before accepting any mutations. Do not use
`task-master parse-prd --force` here as a routine refresh.
