# Test Tree Rules

## Purpose

This directory is the canonical home for all automated tests in Library Ops.
No product test file belongs under `src/libraryops/`. When a test appears to
fit better beside product code, stop and improve the `tests/` topology instead
of creating a local exception.

## Source order

1. Root `AGENTS.md`
2. `tests/AGENTS.md`
3. Child `tests/**/AGENTS.md`
4. `pyproject.toml`
5. `SETUP.md`
6. Current task / PRD acceptance criteria
7. Existing tests in the same subtree

## Topology contract

- Group tests first by test kind, then by module or evaluator flow.
- Current stable kinds are:
  - `control_plane/`
  - `smoke/`
  - `e2e/`
  - `unit/`
  - `integration/`
  - `property/`
- Domain-specific folders may live under `unit/` or `integration/`, but
  new top-level domain-flat folders under `tests/` are not allowed.
- If a directory starts mixing multiple validation regimes, split one level
  deeper rather than extending one monolithic file.
- If a test cannot be placed under an existing kind, stop and decide the
  taxonomy before adding more code.

## Naming rules

- Use one pytest file naming convention only: `test_*.py`.
- Do not introduce `*_test.py`.
- Add package markers (`__init__.py`) when repeated basenames would collide or
  when the subtree benefits from package-local helpers.
- Keep test module names specific to the behavior under test once a subtree
  grows beyond one file.

## Placement rules

- `control_plane/` owns agent workflow, governance, hooks, session notices,
  docs/process gates, and repo policy tests.
- `smoke/` owns deterministic bootstrap and environment checks.
- `e2e/` owns browser flows and evaluator-visible navigation.
- Domain-heavy model/form/query assertions should move toward `unit/`.
- DB-backed orchestration, management commands, and permission-sensitive view
  flows should move toward `integration/`.
- Invariants with varied inputs belong in `property/`.
- When temporary domain folders exist, treat them as migration waypoints, not
  permanent topology.

## Factory and fixture rules

- Reusable object builders belong in `tests/factories/`, split by domain as the
  layer grows.
- Shared pytest fixtures belong in the narrowest possible `conftest.py`.
- E2E-only browser/session helpers belong in `tests/e2e/conftest.py`.
- Truly global guards belong in `tests/conftest.py`.
- Keep one-off helper functions local to the test module unless a second caller
  appears.
- Do not hand-roll browser users or catalog graphs in multiple places once a
  factory exists.

## Assertion rules

- Use plain `assert` in pytest-driven tests unless a Django `TestCase` helper
  adds clear value.
- Use `pytest.raises` for expected exceptions in pytest-managed code paths.
- Keep messages and expectations explicit enough that CI failures localize the
  broken invariant quickly.
- For response-content assertions on non-200 pages, pass the explicit expected
  status code.

## Marker rules

- Files under `tests/e2e/` must use `@pytest.mark.e2e`.
- Property-style tests must use `@pytest.mark.property`.
- Do not add new markers without registering them in `pyproject.toml`.
- Keep marker intent aligned with directory placement.

## Django rules

- Prefer `django.test.TestCase` for DB-heavy Django slices when class grouping
  improves shared setup and readability.
- Prefer pytest functions for property tests and narrowly scoped isolated
  checks.
- Seed role groups explicitly when permissions matter.
- Do not rely on test execution order to create auth groups, seed data, or
  environment state.
- For reverse relations and dynamic Django managers, keep casts or narrow local
  suppressions smaller than the whole file.

## Playwright rules

- Use semantic locators and web-first assertions.
- Keep browser bootstrap in fixtures, not repeated in every test body.
- Treat live-server session bridging as shared test infrastructure.
- Avoid custom browser launch loops when pytest-playwright fixtures already
  provide the surface.
- If async/DB interaction appears, fix the fixture boundary instead of adding
  broad runtime workarounds in product code.

## Type and lint rules

- Product modules under `src/libraryops/` should avoid `TYPE_CHECKING` shims
  unless there is a strong runtime reason; test modules may use them only when
  the alternative is worse than a narrow local import gate.
- Prefer config-level policy first, then narrow local suppressions, then AGENTS
  guidance. Do not weaken whole-repo Pyright or Ruff rules just to land one
  flaky test.
- Keep docstrings on public test helpers, factory classes, and fixture modules;
  the repo enforces docstring coverage and lint.

## Guardrails

- `tests/conftest.py` fails fast if product tests reappear under
  `src/libraryops/`.
- `tests/conftest.py` fails fast if a test file lands outside the kind-first
  top-level directories.
- `tests/control_plane/test_contracts.py` must continue checking that
  `src/libraryops/` stays free of `test_*.py` and `*_test.py`.
- CI and local verification should stop on topology regressions before broader
  pytest runs.

## Escalation

- If a behavior needs a product decision, emit an escalation instead of
  encoding a guess in assertions.
- If a test subtree needs more than one policy family, add a child
  `AGENTS.md`.
- If factories or fixtures become monolithic, split them before adding more
  callers.
