---
id: PRD-LIBRARYOPS-AI
title: Library Ops — Canonical RPG PRD
status: draft-verified-expanded
owner: Engineering
source_of_truth: true
taskmaster_profile: rpg
constitution: .specify/memory/constitution.md
last_reviewed: 2026-06-17
---

# Library Ops — Canonical RPG PRD

## 0. Navigation

- [1. Executive Summary](#1-executive-summary)
- [2. Source-of-Truth and Governance Model](#2-source-of-truth-and-governance-model)
- [3. Standards Profile](#3-standards-profile)
- [4. Socratic Analysis and Ambiguity Log](#4-socratic-analysis-and-ambiguity-log)
- [5. Capability Tree](#5-capability-tree)
- [6. Structural Decomposition](#6-structural-decomposition)
- [7. Dependency Chain](#7-dependency-chain)
- [8. Development Phases](#8-development-phases)
- [9. Requirements](#9-requirements)
- [10. Architecture](#10-architecture)
- [11. Data Model](#11-data-model)
- [12. Search and AI Design](#12-search-and-ai-design)
- [13. Seed Data and Demo Corpus](#13-seed-data-and-demo-corpus)
- [14. UX and Accessibility Workflow](#14-ux-and-accessibility-workflow)
- [15. Agent System and MCP Workflow](#15-agent-system-and-mcp-workflow)
- [16. CI/CD, Branching, and Release Governance](#16-cicd-branching-and-release-governance)
- [17. Security and Privacy](#17-security-and-privacy)
- [18. Verification Strategy](#18-verification-strategy)
- [19. Acceptance Criteria](#19-acceptance-criteria)
- [20. Decision Register](#20-decision-register)
- [21. Risk Register](#21-risk-register)
- [22. Task Master Parsing Contract](#22-task-master-parsing-contract)
- [23. Source Register](#23-source-register)
- [24. Verification Addendum: Tooling, Deployment, and Evidence](#24-verification-addendum-tooling-deployment-and-evidence)

## 1. Executive Summary

### 1.1 Assignment

The assignment is to build a **Mini Library Management System** for the Valsoft interview process.
The original request requires:

- book management: add, edit, and delete books with title, author, and useful metadata;
- check-in/check-out: mark books as borrowed and returned;
- search: find books by title, author, or other fields;
- source code and a brief README explaining how to run it.

The prompt also lists optional bonuses:

- deployed live app URL;
- demo video;
- authentication with SSO, roles, and permissions;
- AI features;
- additional creative features.

Evaluation criteria are completeness, creativity, product quality, and usability.

### 1.2 Product Thesis

**Library Ops** is a compact, production-minded library management demo. It is intentionally smaller
than a real integrated library system, but it should demonstrate mature engineering choices:

- correct library domain modeling;
- opinionated app-based Django organization for models, forms, URLs, views, and templates;
- predictable spec-driven delivery;
- secure role-based operations;
- reproducible seed data;
- lexical search that respects exact library identifiers;
- clear test and CI gates;
- deployable Python/Django implementation;
- kind-first test topology that keeps control-plane, smoke, product, and evaluator evidence distinct;
- agent-compatible implementation workflow using Codex, Task Master, Spec Kit, Context7, Exa, RTK, and governed code-intelligence tooling.

The project is not judged only by feature volume. It is judged by whether an evaluator can see that the
work was decomposed, governed, implemented, tested, and shipped in a disciplined way.

### 1.3 Simplified Scope Decision

The scope has been simplified from a large planning/demo platform into one coherent Django product with
strong supporting meta-systems. The project SHOULD avoid unnecessary enterprise-library features unless
they directly strengthen the interview signal.

The MVP is:

1. catalog and inventory;
2. borrow/return lifecycle;
3. search;
4. auth/RBAC;
5. seed data;
6. deployed demo;
7. README and demo evidence.

The primary bonus is not a broad chatbot. The primary bonus is **Render-native lexical catalog search with
exact-identifier priority, grounded in stored records**.

For the active release-finalization tranche, evaluator-critical work takes
priority over bonus AI scope. Embeddings, AI metadata suggestions, and broader
search experimentation are superseded for the current release
unless they are already merged, tested, and truthfully documented as historical
scope.

### 1.4 Success Metrics

- Evaluator can run the app locally in under 10 minutes after prerequisites are installed.
- Evaluator can use a live deployment with documented disposable demo accounts.
- Minimum assignment flows work end-to-end: create/edit/archive book, borrow, return, search.
- Search returns exact ISBN/barcode matches before fuzzy or keyword matches.
- Member role cannot mutate catalog or circulation through UI or direct POST requests.
- CI validates formatting, linting, typing, architecture imports, migrations, tests, and seed hygiene.
- README maps every assignment criterion to visible evidence.
- Task Master task graph is generated from this PRD and remains traceable.
- Spec Kit constitution and generated specs do not become competing sources of truth.
- Agent tooling decisions identify user tie-back, alternatives, validation evidence, and rollback.
- RTK is required in implementation environments for noisy command-output optimization without replacing raw verification evidence.

### 1.5 Non-Goals

- Full MARC21 cataloging implementation.
- Real production patron privacy/compliance program.
- Fines, payments, procurement, acquisition workflows, or interlibrary loan.
- Multi-branch library administration.
- A generic ungrounded AI chatbot.
- A product AI / vector-search release slice.
- A separate React/Next.js frontend unless scope changes.

## 2. Source-of-Truth and Governance Model

### 2.1 Source-of-Truth Order

1. `.specify/memory/constitution.md` — immutable project principles and governance rules.
2. `.taskmaster/docs/prd.md` — canonical product, architecture, and execution contract.
3. `specs/001-core/*` — supporting Spec Kit artifacts for the core feature scope.
4. `.taskmaster/tasks/tasks.json` — generated Task Master execution graph after parsing the PRD.
5. Current Task Master task/subtask.
6. `AGENTS.md`, nested `AGENTS.md`, and `.codex/agents/*.toml`.
7. `.agents/skills/*/SKILL.md` — progressive-disclosure operating procedures.
8. ADRs and supporting docs under `docs/`.
9. Source code and tests once implemented.

If artifacts conflict, work MUST stop until the conflict is resolved by updating the PRD or constitution.

### 2.2 PRD as Canonical RPG Document

This PRD follows the Repository Planning Graph method from Task Master’s RPG template:

- separate **WHAT** capabilities from **HOW** code structure;
- define explicit dependencies;
- use topological ordering;
- progressively refine capabilities into features and implementation tasks;
- provide test strategy and risk context for generated tasks.

Task Master’s parser should treat each `### Capability:` as a top-level task candidate and each
`#### Feature:` as a subtask candidate. The dependency sections provide sequencing context.
Later capabilities through deployment and release remain in this PRD even while execution is focused on earlier
foundation or product slices.

### 2.3 Spec Kit Relationship

Spec Kit is used for constitution, clarification, and implementation-plan consistency. It does not replace
Task Master as the execution graph. The intended sequence is:

1. update constitution if governance changes;
2. update this PRD;
3. parse/analyze/expand Task Master tasks;
4. generate or refresh Spec Kit artifacts for the selected feature scope;
5. compare Spec Kit output against the PRD/task graph;
6. implement one Task Master task per feature branch.

### 2.4 Documentation Consolidation Policy

The repository SHOULD avoid a sprawling documentation tree. Durable docs are limited to:

- `README.md` for evaluator setup and evidence;
- `AGENTS.md` for agent workflow;
- `.specify/memory/constitution.md` for governance;
- `.taskmaster/docs/prd.md` for product/architecture/execution;
- `docs/runbook.md` for setup/deployment/operations;
- `docs/design/wireframes.md` for implementation-ready UX guidance;
- `docs/adr/*.md` for decision records when a decision deserves independent review.

New docs require a PRD or ADR justification. Routine details should go into code comments, tests, the PRD,
the research/evidence register, or the runbook instead of new standalone documents.

## 3. Standards Profile

The project uses formal standards selectively. The goal is disciplined structure without excessive ceremony.

| Concern | Standard / framework | Project use |
|---|---|---|
| Requirements | ISO/IEC/IEEE 29148-inspired structure | Stakeholders, requirements, acceptance criteria, traceability. |
| Normative terms | RFC 2119 / RFC 8174 | `MUST`, `SHOULD`, `MAY` only when binding. |
| Architecture | C4 + arc42 + pragmatic domain modeling | C4 views for navigation, arc42 quality/risk framing, Django-friendly domain boundaries. |
| Interface | Server-rendered Django views + HTMX | First-party app interaction; no dedicated API surface in the current scope. |
| Security controls | OWASP ASVS | Level 1-style web app security requirements. |
| Security program | OWASP SAMM | Lightweight SDLC security framing. |
| Accessibility | WCAG 2.2 AA | Usability and accessibility baseline. |
| Versioning | SemVer | Releases and changelog. |
| Commits | Conventional Commits | Commitlint and semantic-release input. |
| Agent planning | Task Master RPG + Spec Kit SDD | Predictable AI-assisted implementation. |
| Agent context optimization | RTK + code-intelligence ladder | Noisy-output reduction, graph/symbol/AST planning, raw evidence preservation. |
| Decisioning | Socratic decision framework | User tie-back, alternatives, counterfactual evidence, validation, rollback, and clear pause rules. |
| Evidence discipline | Research register + ADRs | Current-source verification and explicit assumptions. |
| Design-to-code | Repo wireframes | Repo-local implementation source without private design-tool dependence. |

## 4. Socratic Analysis and Ambiguity Log

### Q1. Are we managing books or physical inventory?

**Decision:** The UI may use the word “Book,” but the domain model MUST separate:

- `BibliographicWork` — conceptual work;
- `BookEdition` — publication or edition-level metadata;
- `BookCopy` — borrowable physical/logical item;
- `Loan` — circulation event.

**Reasoning:** A title can have multiple editions and multiple physical copies. A copy is borrowed, not the
abstract title. This mirrors the BIBFRAME Work/Instance/Item abstraction at a pragmatic level without
implementing full BIBFRAME.

**Acceptance impact:** A copy cannot have more than one active loan. Historical loans survive archival.

### Q2. What does “checked in” and “checked out” mean?

**Decision:** Use user-facing labels **Borrow** and **Return**. Internally:

- checkout = borrow an available copy;
- checkin = return an active loan.

**Reasoning:** The assignment wording appears inverted against normal library terminology. The UI avoids
ambiguity while implementation still records the expected state transitions.

**Acceptance impact:** Borrow transitions `AVAILABLE -> ON_LOAN`; return transitions `ON_LOAN -> AVAILABLE`.

### Q3. Is “delete book” a hard delete?

**Decision:** Default behavior is archive/soft-delete. Hard deletion MAY exist only for records with no
historical loans and only for Admins.

**Reasoning:** Hard deletion destroys auditability and makes historical loans misleading.

**Acceptance impact:** Archived records are hidden by default but remain available to Admin/Librarian audit views.

### Q4. Should we use Django Admin as the whole app?

**Decision:** No. Django Admin is useful as an internal management surface, but the evaluator-facing product
MUST include a small first-class UI built with Django templates and HTMX.

**Reasoning:** The assignment evaluates usability. A pure admin interface would look like a framework shortcut,
not a designed product.

### Q5. Should we use Python, Django, or FastAPI?

**Decision:** Use Python with Django and server-rendered templates/HTMX.

**Reasoning:** The assignment is workflow-heavy: auth, roles, admin, forms, database models, migrations,
management commands, and deployment. Django standardizes more of this than a custom FastAPI stack, while
server-rendered templates keep the implementation aligned with the evaluator-facing UX.

### Q6. Should search be vector-only?

**Decision:** No. Search MUST be exact-identifier-first lexical search with PostgreSQL full-text ranking.

**Reasoning:** In library systems, ISBNs, barcodes, Open Library IDs, titles, and author names are high-precision
signals. The current release stays deterministic and testable without a semantic/vector layer.

### Q7. Should ParadeDB be required?

**Decision:** No. Baseline search uses PostgreSQL full-text search only.

**Reasoning:** The release must remain reliable on standard Postgres. Extra search adapters add deployment
coupling without improving the current evaluator path.

### Q8. Which embedding strategy should be default?

**Decision:** No embedding pipeline is part of the current release.

**Reasoning:** The release goal is a grounded, reproducible evaluator path. Any future ML workflow must be
planned explicitly rather than carried in as a hidden dependency.

### Q9. Should AI generate catalog data automatically?

**Decision:** No. The current release does not include AI-generated catalog data or metadata suggestions.

**Reasoning:** The active scope stays focused on deterministic catalog, circulation, search, and evidence flows.

### Q10. Should demo passwords be public?

**Decision:** Disposable demo credentials MAY be documented.

**Reasoning:** These accounts exist only in seeded demo data and can be reset. Real secrets remain prohibited.

### Q11. Should a private design tool be mandatory?

**Decision:** The repo MUST contain implementation-ready wireframes. Private
design tools do not form part of the committed implementation baseline.

**Reasoning:** A private design artifact must not block source review or
implementation. Important design decisions must be mirrored back into repo docs.

### Q12. How do we prevent agent drift?

**Decision:** Agents MUST work from the constitution, PRD, Task Master task, and relevant skill. Work not tied
to a task should be rejected or converted into a PRD/task update first.

### Q13. Should RTK be deeply integrated?

**Decision:** Yes. RTK is a required implementation-environment optimization for Codex shell-output/context management.

**Reasoning:** The user explicitly requested deep RTK integration. RTK should reduce noisy command output, but it must not become a substitute for raw evidence.

**Acceptance impact:** Agent instructions, skills, runbooks, Codex hooks, and validation scripts must integrate RTK. Strict tooling verification fails in implementation environments when RTK is absent. Raw reruns or full logs remain required for ambiguous failures, security findings, release evidence, and final verification.

### Q14. Which code-intelligence/MCP tools are required?

**Decision:** The selected local implementation stack is required: code-review-graph for graph/blast-radius review, Serena for symbol-level retrieval/refactor planning, ast-grep for deterministic structural search, Repomix for bounded repo packs, Context7 and Exa for research, and Task Master MCP/CLI for execution.

**Reasoning:** The user clarified that these should not remain vague optional add-ons. Alternatives were examined across smaller dedicated tools, larger hosted platforms, and raw/manual workflows. The project chooses local-first tools by default and defers hosted/cloud code-indexing, paid dashboards, and broader context layers until an explicit user decision.

**Acceptance impact:** `.codex/config.toml`, skills, hooks, docs, and validation scripts declare the selected stack. Strict tooling verification fails in implementation environments when required tools are missing. Details live in `AGENTS.md`, capability-matched skills, ADR-0004, and ADR-0007.

### Q15. How should evaluator-facing Django UI code be organized?

**Decision:** Favor app-owned Django UI slices. Product apps SHOULD own their own `urls.py`, view modules/packages, and
template namespaces when they expose evaluator-facing flows. The shared `web` app remains the thin shell for landing,
home, navigation, and reusable presentation helpers rather than becoming a monolithic destination for every view.

**Reasoning:** The project is growing beyond a single `views.py` surface. App-based URL/view/template ownership makes
catalog, circulation, and future flows easier to review, test, and evolve without mixing unrelated concerns into one
catch-all UI layer.

**Acceptance impact:** `config/urls.py` composes app URLConfs; non-trivial UI surfaces are split by app and page family;
templates use explicit app namespaces such as `templates/web/`, `templates/catalog/`, and `templates/circulation/`.

### Q16. What is the durable test-topology direction?

**Decision:** Keep all automated tests under `tests/` and group them first by test kind, then by module or evaluator
flow. `tests/control_plane/`, `tests/smoke/`, and `tests/e2e/` are current stable anchors. Domain folders are
transitional waypoints that should migrate toward `tests/unit/`, `tests/integration/`, and `tests/property/`.

**Reasoning:** Kind-first organization keeps meta-system checks, bootstrap checks, domain invariants, DB-backed
orchestration, and evaluator-visible browser flows distinct. That lowers review friction and keeps future test growth
from collapsing into monolithic domain buckets.

**Acceptance impact:** New tests are placed by validation regime first; product tests do not return to `src/libraryops/`;
temporary domain folders are treated as migration waypoints rather than the desired end state.

## 5. Capability Tree

The capability tree intentionally keeps the end-to-end path visible from foundation through deployment, release
evidence, and reusable process capture. Current execution may be focused on an earlier capability, but later delivery
capabilities remain planned here so Task Master regeneration preserves the full route to a shipped demo.

### Capability: C1 Project Foundation

Create a reproducible, agent-friendly project foundation.

**Depends on:** []

#### Feature: C1.F1 Repository and toolchain baseline

- **Description:** Initialize the Python/Django repository baseline, toolchain, and verification scripts.
- **Inputs:** Existing control-plane package bootstrap, Python 3.12+, Node 20+, uv, GitHub repository.
- **Outputs:** Verified repository with documented bootstrap and local quality gates.
- **Behavior:** Provide deterministic setup commands and enforce no-junk/no-secret hygiene.
- **Acceptance criteria:**
  - `codex doctor --summary --ascii --no-color` reports a healthy local control-plane state.
  - `uv sync --all-groups` succeeds.
  - `npm install` or `npm ci` succeeds.
  - `.pytest_cache`, `.venv`, corpora, model caches, and secrets are not committed.

#### Feature: C1.F2 Django project bootstrap

- **Description:** Harden the existing Django project under `src/libraryops/config` with local/test/production settings, real `DATABASE_URL` support, and root URL composition that can mount app-owned URLConfs cleanly.
- **Inputs:** Existing `manage.py`, `src/libraryops/config/*`, `pyproject.toml`, environment variables, database URL.
- **Outputs:** Verified settings modules, root URL config, WSGI/ASGI config, and smoke-testable bootstrap.
- **Behavior:** Local settings support development, test settings respect `DATABASE_URL` when present, production settings require explicit secure environment, and root routing stays thin enough to compose app-based UI surfaces.
- **Acceptance criteria:**
  - `uv run python manage.py check` succeeds.
  - SQLite remains the fallback when `DATABASE_URL` is absent.
  - Postgres is selected when `DATABASE_URL` is set.
  - `/health/` smoke tests pass under the test settings.
  - Missing required production env vars fail loudly.

#### Feature: C1.F3 Quality tools

- **Description:** Configure Ruff, Pyright, pytest, Hypothesis, Import Linter, coverage, pip-audit, markdownlint.
- **Inputs:** `pyproject.toml`, package configuration, GitHub workflows.
- **Outputs:** Local and CI quality gates.
- **Behavior:** Gates fail on real violations and skip only where bootstrap is not yet present.
- **Acceptance criteria:**
  - Ruff format/lint runs.
  - Pyright runs with strict defaults and pragmatic exceptions documented.
  - Import Linter enforces module boundaries once Django apps exist.

#### Feature: C1.F4 Agent, MCP, and context baseline

- **Description:** Configure Codex, Task Master, Spec Kit, Context7, Exa, RTK-aware operating rules, and bounded context budgets.
- **Inputs:** `.codex/config.toml`, `AGENTS.md`, skills, MCP credentials in local environment only.
- **Outputs:** Agent-compatible project workspace with secrets excluded and coordinator-root context contract set to `500,000` tokens.
- **Behavior:** Agents can research current docs, inspect Task Master tasks, use design context, optimize noisy shell output with RTK, and preserve raw evidence.
- **Acceptance criteria:**
  - MCP examples document required local authentication.
  - No real MCP keys are committed.
  - Repo wireframes remain the non-private implementation source.
  - `default_permissions` and root context settings remain root-scoped in `.codex/config.toml`.
  - Main agent context contract is documented and validated as `500,000` tokens.
  - Subagent context budgets are bounded, and bounded child-worker fan-out is
    allowed when a slice branches.

#### Feature: C1.F5 Code-intelligence and Socratic tooling governance

- **Description:** Add decision-governed support for RTK, code graph, symbol retrieval, AST search, repo snapshots, MCP/tool alternatives, and the current meta-system hardening priorities.
- **Inputs:** `AGENTS.md`, `.agents/skills/code-intelligence/SKILL.md`, `.codex/agents/code-intelligence-architect.toml`, and the current docs hub surfaces.
- **Outputs:** Code-intelligence skill/agent, documented tool ladder, focused meta-system regression coverage, validation scripts, and explicit pause rules for trust/cost/scope changes.
- **Behavior:** Agents evaluate context/tooling choices through accepted/recommended/ask/deferred decision statuses, tie material changes back to user decisions, and keep source-order/routing/tooling checks ahead of deeper product implementation assumptions.
- **Acceptance criteria:**
  - RTK is documented as required in implementation environments and raw evidence rules are explicit.
  - code-review-graph is configured as a required project MCP with restricted graph/review tools.
  - Serena, ast-grep, Repomix, agent-skills-lint, actionlint, zizmor, Conftest, tokenix, Headroom, LeanCTX, and cloud semantic-code stores are classified.
  - `npm run checks:precommit`, `npm run taskmaster:validate`, and the focused hook/agent tests surface local tooling and meta-system regressions without custom verifier wrappers.
  - `codex doctor --summary --ascii --no-color` plus direct tool probes validate agent, skill, docs, context settings, and TOML/config health.
  - The hardening priority order is explicit: source-of-truth alignment, required-tool/runtime verification, coordinator and skill routing correctness, continuation/evidence surface integrity, and focused governance-test coverage.

### Capability: C2 Library Domain Model

Represent library catalog, inventory, circulation, audit, and source provenance.

**Depends on:** [C1]

#### Feature: C2.F1 Bibliographic work and contributor models

- **Description:** Model conceptual works and contributors.
- **Inputs:** Catalog imports, user-created records.
- **Outputs:** `BibliographicWork`, `Contributor`, `WorkContributor` records.
- **Behavior:** Works can have multiple contributors with role and order.
- **Acceptance criteria:**
  - Work has required title.
  - Contributors can be author, editor, translator, illustrator, or other role.
  - Normalized title and contributor names support search.

#### Feature: C2.F2 Edition model

- **Description:** Model edition/publication metadata.
- **Inputs:** Manual forms, Open Library dumps, Gutenberg metadata.
- **Outputs:** `BookEdition` records.
- **Behavior:** Edition stores ISBN-10/ISBN-13, publisher, publication year, language, subjects, identifiers, cover URL, and description.
- **Acceptance criteria:**
  - Valid ISBNs are normalized.
  - Invalid ISBNs fail validation.
  - External IDs are stored as structured JSON.

#### Feature: C2.F3 Inventory copy model

- **Description:** Model borrowable copies.
- **Inputs:** Librarian-created copies, seed generation.
- **Outputs:** `BookCopy` records.
- **Behavior:** Each copy has barcode, status, shelf location, condition note, and archival state.
- **Acceptance criteria:**
  - Barcode is unique.
  - Copy status is one of `AVAILABLE`, `ON_LOAN`, `MAINTENANCE`, `LOST`, `ARCHIVED`.

#### Feature: C2.F4 Loan model and constraints

- **Description:** Model circulation events with database-level invariants.
- **Inputs:** Checkout/return service calls.
- **Outputs:** `Loan` records.
- **Behavior:** Only one active loan may exist per copy.
- **Acceptance criteria:**
  - Partial unique constraint prevents duplicate active loans.
  - Returned loans remain visible historically.

#### Feature: C2.F5 Audit and provenance models

- **Description:** Track privileged mutations and imported-data provenance.
- **Inputs:** Service-layer mutations and import commands.
- **Outputs:** `AuditEvent` and `ExternalSourceRecord` records.
- **Behavior:** Audit events are append-only from application code.
- **Acceptance criteria:**
  - Create/edit/archive/borrow/return actions write audit events.
  - Imported records include source, source identifier, fetched/imported timestamp, and license note.

### Capability: C3 Authentication and RBAC

Support role-based app access with Admin, Librarian, and Member roles.

**Depends on:** [C1, C2]

#### Feature: C3.F1 Django auth and groups

- **Description:** Use Django auth with groups/permissions for role mapping.
- **Inputs:** Demo users, admin-created users, allauth accounts.
- **Outputs:** Authenticated users with application role.
- **Behavior:** Users are assigned to exactly one application role group.
- **Acceptance criteria:**
  - Admin, Librarian, Member groups are seeded.
  - Every demo user has exactly one role.

#### Feature: C3.F2 Server-side authorization services

- **Description:** Provide permission checks used by views, APIs, and services.
- **Inputs:** `request.user`, role, operation, target object.
- **Outputs:** allow/deny decision or exception.
- **Behavior:** UI and API both call shared authorization utilities.
- **Acceptance criteria:**
  - Member direct POST to mutate catalog fails.
  - Anonymous direct POST fails.
  - Librarian can mutate catalog/circulation but not manage roles.

#### Feature: C3.F3 OAuth-ready SSO

- **Description:** Configure django-allauth so deployed demo can support social login when credentials are supplied.
- **Inputs:** OAuth provider client ID/secret from environment.
- **Outputs:** OAuth login flow.
- **Behavior:** Local demo can run with username/password; OAuth is optional and environment-driven.
- **Acceptance criteria:**
  - App runs without OAuth secrets.
  - README explains optional OAuth setup.

### Capability: C4 Catalog Management

Provide evaluator-facing catalog workflows and internal admin support.

**Depends on:** [C2, C3]

#### Feature: C4.F1 Catalog browse and detail pages

- **Description:** Show books, editions, contributors, copies, availability, and allowed actions.
- **Inputs:** Catalog records, current user role, search/filter state.
- **Outputs:** App-owned catalog URL, views, and templates with role-aware actions.
- **Behavior:** Anonymous/member users can view; librarians/admins see management actions; catalog UI remains organized under catalog-owned routes and templates rather than a shared monolithic view file.
- **Acceptance criteria:**
  - Book list has empty/loading/error states where relevant.
  - Book detail shows availability from copy state.

#### Feature: C4.F2 Create/edit/archive forms

- **Description:** Allow Admin/Librarian to manage works, editions, and copies.
- **Inputs:** Form data, current user.
- **Outputs:** Persisted records and audit events.
- **Behavior:** Validate form fields and execute mutations through services.
- **Acceptance criteria:**
  - Required fields are enforced.
  - Archive hides records from default catalog results.
  - Audit event records before/after fields where practical.

#### Feature: C4.F3 Cover image support

- **Description:** Support external cover URLs and optional uploaded cover images.
- **Inputs:** Open Library cover URL, user-uploaded JPEG/PNG/WebP.
- **Outputs:** Stored cover reference and thumbnail.
- **Behavior:** Uploaded images are size/type validated and associated with an edition.
- **Acceptance criteria:**
  - Non-image uploads are rejected.
  - Oversized uploads are rejected.
  - Cover changes are audited.

#### Feature: C4.F4 Django Admin configuration

- **Description:** Configure Django Admin for trusted internal management.
- **Inputs:** Models and permissions.
- **Outputs:** Admin screens with useful list filters/search.
- **Behavior:** Admin supplements, not replaces, the product UI.
- **Acceptance criteria:**
  - Admin list views support search by title, contributor, ISBN, barcode.
  - Admin permissions align with role policy.

### Capability: C5 Circulation

Implement checkout/borrow and checkin/return lifecycle.

**Depends on:** [C2, C3, C4]

#### Feature: C5.F1 Checkout service

- **Description:** Checkout an available copy to a Member with a due date.
- **Inputs:** copy ID/barcode, patron user, librarian/admin actor, due date.
- **Outputs:** Active `Loan` and copy state `ON_LOAN`.
- **Behavior:** Execute in a transaction and fail on unavailable copies.
- **Acceptance criteria:**
  - Available copy can be checked out.
  - Unavailable/lost/maintenance/archive copy cannot be checked out.
  - Duplicate active loan is impossible.

#### Feature: C5.F2 Return service

- **Description:** Return a copy with an active loan.
- **Inputs:** loan ID or copy barcode, actor.
- **Outputs:** Closed loan and copy state `AVAILABLE`.
- **Behavior:** Execute in a transaction and fail when no active loan exists.
- **Acceptance criteria:**
  - Active loan can be returned.
  - Return without active loan fails gracefully.

#### Feature: C5.F3 Circulation UI

- **Description:** Provide checkout/return workflows for librarians/admins.
- **Inputs:** Book detail actions, copy barcode, patron search, due date.
- **Outputs:** App-owned circulation URL, views, and HTML/HTMX modal or page response.
- **Behavior:** Use progressive enhancement; actions work without large frontend framework; circulation-specific routes/templates stay with the circulation surface rather than accumulating inside a generic web layer.
- **Acceptance criteria:**
  - Checkout can be completed from book detail or circulation page.
  - Return can be completed from active loans dashboard.

#### Feature: C5.F4 Loan dashboard

- **Description:** Show active loans, overdue loans, and recent returns.
- **Inputs:** Loan data, role.
- **Outputs:** Dashboard cards and tables.
- **Behavior:** Members see their own loans; librarians/admins see all loans.
- **Acceptance criteria:**
  - Overdue status is derived from `due_at` and `returned_at`.
  - Member cannot see other members’ loans.

### Capability: C6 Search and Discovery

Provide exact-identifier-first lexical catalog search with PostgreSQL full-text ranking and filters.

**Depends on:** [C2, C4]

#### Feature: C6.F1 Exact identifier search

- **Description:** Prioritize ISBN-10, ISBN-13, barcode, Open Library ID, Gutenberg ID, and internal IDs.
- **Inputs:** Query string.
- **Outputs:** Ranked exact-match results.
- **Behavior:** Normalize identifiers and return exact matches before other search modes.
- **Acceptance criteria:**
  - Exact ISBN ranks first.
  - Exact barcode routes directly to copy/edition context.

#### Feature: C6.F2 PostgreSQL full-text search

- **Description:** Use weighted `tsvector` and `websearch_to_tsquery`/safe query construction for keyword search.
- **Inputs:** Normalized query and filters.
- **Outputs:** Keyword-ranked results.
- **Behavior:** Title/contributor weights exceed subjects/tags, which exceed description.
- **Acceptance criteria:**
  - Title and author searches work case-insensitively.
  - Description/subject matches work but do not outrank exact title/author matches.

#### Feature: C6.F3 Facets and filters

- **Description:** Add filters for availability, contributor, subject/genre, language, and source.
- **Inputs:** Search query and selected facets.
- **Outputs:** Filtered result set and facet counts.
- **Behavior:** Facets update with search context.
- **Acceptance criteria:**
  - Availability filter is database-derived.
  - Empty facets do not break search.

#### Feature: C6.F4 Deterministic ranking and explanations

- **Description:** Merge exact and FTS results with deterministic ranking and human-readable explanations.
- **Inputs:** Result lists and ranks.
- **Outputs:** Ranked results and explanation text.
- **Behavior:** Exact identifiers outrank keyword matches, and available copies can be boosted without hiding exact matches.
- **Acceptance criteria:**
  - Ranking is deterministic for the same dataset/query.
  - Exact identifier match always outranks keyword-only results.
  - Explanations describe why a result matched.

### Capability: C7 Superseded Product AI

This capability is retained only as historical context. It is **not part of the current release** and must not
produce active implementation tasks for the evaluator release.

**Depends on:** [C6]

- Historical vector/embedding and AI-assist ideas are superseded by the current lexical-search release scope.
- If a later release reintroduces AI, update the PRD and task graph deliberately rather than reviving this section by habit.

### Capability: C8 Seed Data and Demo Dataset

Create reproducible demo data with recognized public-domain works and disposable users.

**Depends on:** [C2, C3]

#### Feature: C8.F1 Demo roles and users

- **Description:** Seed Admin, Librarian, and Member demo accounts.
- **Inputs:** Management command args.
- **Outputs:** Disposable users with documented credentials.
- **Behavior:** Resettable and idempotent.
- **Acceptance criteria:**
  - `admin@libraryops.demo`, `librarian@libraryops.demo`, and `member@libraryops.demo` exist.
  - Passwords can be reset with seed command.

#### Feature: C8.F2 Public-domain catalog import

- **Description:** Import up to 1,000 curated public-domain-recognizable records.
- **Inputs:** Open Library dumps and/or Project Gutenberg metadata.
- **Outputs:** Works, editions, contributors, provenance records.
- **Behavior:** Prefer bulk dumps/catalogs over API scraping.
- **Acceptance criteria:**
  - Import supports `--source`, `--limit`, `--dry-run`, and `--refresh`.
  - Records include source and license/copyright note.
  - Subject metadata is preserved in imported source data when available, but dedicated subject entities are not yet part of the current release slice.

#### Feature: C8.F3 Copies and loan examples

- **Description:** Generate realistic copies and example active/returned/overdue loans.
- **Inputs:** Imported catalog and demo users.
- **Outputs:** Inventory and circulation demo state.
- **Behavior:** Deterministic seed using fixed seed value.
- **Acceptance criteria:**
  - Dashboard has visible active and overdue loan examples.
  - Search results show available and unavailable books.

### Capability: C9 Release Evidence and Review Surfaces

Keep evaluator-facing evidence in the README, runbook, deployment checks, demo materials, and review
tracking. No dedicated API layer is planned in the current scope.

### Capability: C10 Deployment and Demo Evidence

Ship a live, reviewable product and documentation evidence.

**Depends on:** [C1, C2, C3, C4, C5, C6, C7, C8]

#### Feature: C10.F1 Render deployment

- **Description:** Deploy Django app to Render or equivalent Python-friendly host.
- **Inputs:** GitHub repository, environment variables, managed Postgres.
- **Outputs:** Live app URL.
- **Behavior:** Deploy from `main` after CI passes and release readiness is proven.
- **Acceptance criteria:**
  - Live URL loads.
  - Static assets are served.
  - Database migrations run through a deterministic host-appropriate path.
  - Free-tier Render deployment does not rely on `preDeployCommand`.

#### Feature: C10.F2 README evaluator evidence

- **Description:** Update README with live URL, demo accounts, feature checklist, setup, and tests.
- **Inputs:** Implemented features and deployment output.
- **Outputs:** Evaluator-ready README.
- **Behavior:** Map assignment criteria to evidence.
- **Acceptance criteria:**
  - README includes local setup, demo users, test commands, deployment URL, and known limitations.

#### Feature: C10.F3 Demo script and release tag

- **Description:** Prepare Loom/demo script and tag a release.
- **Inputs:** Final app and README.
- **Outputs:** Demo script, video link, SemVer release tag.
- **Behavior:** Demo covers product, architecture, tests, and tradeoffs.
- **Acceptance criteria:**
  - Release tag corresponds to deployed commit.
  - Demo script can be completed in 3–6 minutes.

### Capability: C11 Documentation, Evidence, and Reusable Process

- **Purpose:** Maintain evaluator-facing and agent-facing documentation that proves what was planned,
  researched, implemented, tested, deployed, and learned.
- **Depends on:** [C1]
- **Priority:** P1 throughout the project; P0 for README/runbook essentials.

#### Feature: C11.F1 Research and evidence discipline

- **Description:** Keep primary-source findings, assumptions, implementation-time checks, and decision
  impact in the PRD source register, ADRs, and concise Task Master notes rather than a separate
  historical evidence document set.
- **Acceptance:** Material external claims in the PRD/ADRs can be traced to source-register entries,
  ADRs, Task Master notes, or explicit assumptions.

#### Feature: C11.F2 Context drift review

- **Description:** Maintain a short review of what changed between major control-plane package/project revisions and which
  decisions were preserved.
- **Acceptance:** Future agents can understand what context was inherited, what changed, and which caveats remain.

#### Feature: C11.F3 Deployment evidence package

- **Description:** Keep README/runbook evidence current with live URL, demo credentials, smoke-test checklist,
  quality gates, release tag, and known limitations.
- **Acceptance:** An evaluator can verify the deployed app and understand how it was built without reading the
  entire PRD.

#### Feature: C11.F4 Reusable SDLC pattern

- **Description:** Document the governance pattern—constitution, RPG PRD, Task Master, Spec Kit, ADRs, CI gates,
  research register, and runbook—so it can scale to other projects.
- **Acceptance:** The project explains which process artifacts are project-specific and which can be reused.

### Capability: C12 Context Recovery and Planning Hygiene

- **Purpose:** Keep long-horizon planning synchronized with user direction by re-gathering durable context from
  previous compacts, prior conversations, memory surfaces, and external context packs when accessible, then
  converting durable findings into Task Master tasks and tracked docs.
- **Depends on:** [C11]
- **Priority:** P1 ongoing; P0 whenever scope drift or missing context is detected.

#### Feature: C12.F1 Context re-grounding

- **Description:** Reconstruct the current planning baseline from prior compacts, user messages, and durable
  repository surfaces before broadening into new work.
- **Acceptance:** The active plan reflects the latest durable user intent and identifies any gaps or stale claims.

#### Feature: C12.F2 Task synthesis from durable findings

- **Description:** Convert durable findings into Task Master tasks, subtasks, or notes instead of leaving them as
  untracked chat history.
- **Acceptance:** New or revised scope appears in Task Master with concise evidence and a bounded owner.

#### Feature: C12.F3 Meta-surface reconciliation

- **Description:** Update PRD, phase docs, AGENTS, and related governance surfaces when the same lesson repeats
  or the planning model shifts.
- **Acceptance:** Repeated planning lessons are promoted into tracked repo docs or skills rather than staying
  memory-only.

## 6. Structural Decomposition

### 6.1 Repository Structure

The target repository shape for the Django product is:

```text
library-ops/
  README.md
  AGENTS.md
  pyproject.toml
  uv.lock
  manage.py
  env.example
  .specify/memory/constitution.md
  .taskmaster/docs/prd.md
  .taskmaster/tasks/                  # derived execution graph; tasks.json is committed, runtime notes stay local
  .codex/config.toml
  .agents/skills/
  docs/runbook.md
  docs/design/wireframes.md
  docs/adr/
  src/libraryops/
    config/
    core/
    accounts/
    catalog/
      urls.py
      views/
    inventory/
    circulation/
      urls.py
      views/
    search/
    audit/
    web/
      urls.py
      views/
  templates/
    web/
    catalog/
    circulation/
  static/
  tests/e2e/
  tests/property/
```

### 6.2 Module Definitions

#### Module: `core`

- **Maps to capability:** C1 Project Foundation.
- **Responsibility:** Shared primitives with no application dependency.
- **Exports:** time helpers, ID helpers, result/error types, common exceptions.
- **Dependencies:** none except standard library and stable third-party primitives.

#### Module: `accounts`

- **Maps to capability:** C3 Authentication and RBAC.
- **Responsibility:** role initialization, demo-user seeding, permissions, profile-level helpers.
- **Exports:** `require_librarian`, `require_admin`, `can_manage_catalog`, `can_manage_circulation`.
- **Dependencies:** `core` and Django auth.

#### Module: `catalog`

- **Maps to capability:** C2/C4 catalog domain.
- **Responsibility:** works, editions, contributors, provenance-backed imports, and catalog-owned Django forms, URLs, views, templates, and import helpers.
- **Exports:** catalog selectors and mutation services.
- **Dependencies:** `core`, `accounts`, `audit`.

#### Module: `inventory`

- **Maps to capability:** C2 copy inventory.
- **Responsibility:** copies, barcode rules, inventory state.
- **Exports:** copy selectors and services.
- **Dependencies:** `core`, `catalog`, `audit`.

#### Module: `circulation`

- **Maps to capability:** C5 circulation.
- **Responsibility:** checkout, return, loans, overdue calculations, and circulation-owned route/view/template flows.
- **Exports:** `checkout_copy`, `return_copy`, loan selectors.
- **Dependencies:** `core`, `accounts`, `inventory`, `audit`.

#### Module: `search`

- **Maps to capability:** C6 search.
- **Responsibility:** exact identifier lookup, PostgreSQL full-text search, facet filtering, deterministic ranking.
- **Exports:** `search_catalog`.
- **Dependencies:** `core`, `catalog`, `inventory`.

#### Module: `audit`

- **Maps to capability:** C2 audit/provenance.
- **Responsibility:** append-only audit events and external source records.
- **Exports:** `record_audit_event`, `record_source_provenance`.
- **Dependencies:** `core`, `accounts` only where actor references are required.

#### Seed workflows

- **Maps to capability:** C8 seed data.
- **Responsibility:** app-owned management commands for demo roles/users, public-domain import/provenance, and circulation examples; no standalone `seed` app directory.
- **Exports:** management commands and importer/rebuild services in the owning app modules.
- **Dependencies:** domain modules, not web views.

#### Module: `web`

- **Maps to capability:** C4/C5/C6 presentation.
- **Responsibility:** landing/home composition, shared navigation, view models, and presentation utilities.
- **Exports:** navigation context, display formatting helpers.
- **Dependencies:** selectors/services, not low-level persistence details.
- **Boundary:** `web` SHOULD stay thin and SHOULD NOT become the default home for unrelated catalog or circulation views once app-owned UI slices exist.

### 6.3 Layering Rules

- `domain.py` contains pure business rules and no database/network calls.
- `models.py` contains persistence schema and simple invariants.
- `selectors.py` contains read queries only.
- `services.py` contains transactional mutations.
- `forms.py` validates template flows.
- `urls.py` belongs to the owning Django app when that app exposes evaluator-facing routes.
- non-trivial UI surfaces SHOULD use `views/` packages or split modules by page/flow family instead of one growing `views.py`.
- templates live under explicit app namespaces such as `templates/web/`, `templates/catalog/`, and `templates/circulation/`.
- `config/urls.py` composes app URL trees and cross-cutting endpoints rather than becoming a feature catch-all.
- views orchestrate HTTP/template behavior and delegate rules to services/selectors.
- `admin.py` configures internal admin only.

## 7. Dependency Chain

### Foundation Layer — Phase 0

- `core`: no app dependencies.
- `config`: Django settings and environment loading.
- tooling/CI/agent system: no app dependencies.

### Domain Layer — Phase 1

- `accounts`: depends on `core` and Django auth.
- `audit`: depends on `core` and optional `accounts` actor references.
- `catalog`: depends on `core`, `accounts`, `audit`.
- `inventory`: depends on `core`, `catalog`, `audit`.

### Circulation and Search Layer — Phase 2

- `circulation`: depends on `core`, `accounts`, `inventory`, `audit`.
- `search`: depends on `core`, `catalog`, `inventory`.

### Presentation Layer — Phase 3

- `web`: depends on selectors/services.
- `templates`: depend on view contexts only.

### Deployment/Demo Layer — Phase 4

- deployment depends on all core flows and seed data.
- README/demo evidence depends on implementation and deployment.

## 8. Development Phases

These phases remain represented in the PRD from foundation through deployment and release evidence even when the current
implementation task is earlier in the chain. Future steps are planned up front so task regeneration and review do not
lose the path to a deployed demo.

### Phase 0: Governance and Foundation

**Goal:** Make the repo safe and predictable before app code.

**Entry criteria:** Control-plane package archive unzipped, git initialized, clean working tree.

**Tasks:**

- update PRD, constitution, AGENTS, runbook, design notes;
- remove generated junk from repo;
- verify scripts and CI are accurate;
- initialize Task Master and Spec Kit in-place;
- lock meta-system hardening priorities and kind-first test-direction rules into the canonical docs/tests surfaces;
- create feature branch workflow.

**Exit criteria:**

- control-plane package verification passes;
- PRD can be parsed by Task Master;
- current task graph has no circular dependencies;
- focused governance and smoke checks cover the meta-system and bootstrap surfaces that exist;
- CI skeleton is ready.

**Delivers:** An implementable plan and governed agent workspace.

### Phase 1: Django Bootstrap, Domain, and RBAC

**Goal:** Build the application base, domain model, and roles.

**Entry criteria:** Phase 0 complete; Task Master tasks generated.

**Tasks:**

- bootstrap Django project;
- establish app-owned route/view/template skeletons for the first evaluator-facing flows;
- implement models/migrations;
- seed roles/users;
- implement permission services;
- add domain/constraint tests and begin the kind-first test migration away from temporary domain buckets.

**Exit criteria:**

- `manage.py check` passes;
- migrations apply;
- demo users exist;
- model constraints are tested.

**Delivers:** A correct foundation for assignment flows.

### Phase 2: Core Assignment Features

**Goal:** Complete catalog management, borrow/return, and search MVP.

**Entry criteria:** Phase 1 complete.

**Tasks:**

- catalog list/detail/create/edit/archive;
- copy management;
- checkout/return services and UI;
- baseline exact/FTS search;
- audit events.

**Exit criteria:**

- evaluator can complete required flows locally;
- role boundaries are enforced;
- property tests cover loan invariants.

**Delivers:** Assignment-complete product.

### Phase 3: Bonus Quality Features

**Goal:** Add high-signal bonus features without destabilizing the app.

**Entry criteria:** Phase 2 complete.

**Tasks:**

- public-domain seed corpus;
- cover image upload;
- exact-identifier search quality regression tests;
- PostgreSQL full-text ranking and filter coverage;
- Playwright E2E suite.

**Exit criteria:**

- lexical search works on seeded corpus;
- generated/demo data is reproducible;
- E2E tests cover core flows.

**Delivers:** Creativity and product-quality evidence.

### Phase 4: Deployment and Demo

**Goal:** Ship a live reviewable demo.

**Entry criteria:** Phase 3 complete or intentionally trimmed with documented known limitations.

**Tasks:**

- deploy to Render or equivalent;
- configure production env vars;
- run migrations/seed;
- update README;
- create demo script;
- tag release.

**Exit criteria:**

- live URL works;
- demo accounts work;
- README maps requirements to evidence;
- release tag maps to deployed commit.

**Delivers:** Interview-ready submission.

## 9. Requirements

The key words `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, `MAY`, and `OPTIONAL` are to be interpreted as in RFC 2119 and RFC 8174 only when written in uppercase.

### 9.1 Functional Requirements

| ID | Requirement |
|---|---|
| FR-001 | The system MUST allow Admins and Librarians to create catalog records with title and contributor/author information. |
| FR-002 | The system MUST allow Admins and Librarians to edit catalog metadata. |
| FR-003 | The system MUST allow Admins and Librarians to archive catalog records. |
| FR-004 | The system MUST model copies separately from editions/works. |
| FR-005 | The system MUST allow Admins and Librarians to checkout an available copy to a Member. |
| FR-006 | The system MUST prevent more than one active loan for a copy. |
| FR-007 | The system MUST allow Admins and Librarians to return an active loan. |
| FR-008 | The system MUST provide search by title and author/contributor. |
| FR-009 | The system SHOULD provide search by ISBN, barcode, subject, description, language, and source. |
| FR-010 | Exact identifiers MUST outrank keyword search results. |
| FR-011 | The system SHOULD provide role-based navigation and server-side authorization. |
| FR-012 | The system SHOULD provide disposable demo accounts. |
| FR-013 | The system SHOULD import a reproducible public-domain-oriented demo corpus. |
| FR-014 | Historical AI-assisted metadata suggestions are out of current release scope. |
| FR-015 | No AI-generated metadata is persisted in the current release scope. |
| FR-016 | Availability MUST always be derived from database copy/loan state. |

### 9.2 Non-Functional Requirements

| ID | Area | Requirement |
|---|---|---|
| NFR-001 | Usability | Core evaluator flows SHOULD be discoverable without reading code. |
| NFR-002 | Accessibility | UI SHOULD target WCAG 2.2 AA for forms, navigation, focus, labels, and contrast. |
| NFR-003 | Security | Privileged operations MUST enforce authorization server-side. |
| NFR-004 | Security | Secrets MUST NOT be committed. |
| NFR-005 | Reliability | Checkout and return MUST be transactional. |
| NFR-006 | Reliability | Database constraints MUST enforce active-loan uniqueness. |
| NFR-007 | Maintainability | Business rules SHOULD live in domain/services, not views/templates. |
| NFR-008 | Testability | Loan lifecycle invariants SHOULD be covered by property-based tests. |
| NFR-009 | Portability | The app SHOULD run locally without hosted AI credentials. |
| NFR-010 | Observability | Mutating catalog/circulation operations SHOULD produce audit events. |

### 9.3 Traceability to Assignment

| Assignment criterion | PRD capabilities | Evidence target |
|---|---|---|
| Book management | C2, C4 | catalog UI, admin, tests |
| Add/edit/delete | C4 | create/edit/archive flows |
| Check-in/check-out | C5 | borrow/return flows and invariant tests |
| Search | C6 | exact/FTS search |
| Working product | C1–C10 | local run + live deployment |
| README | C10 | evaluator-ready README |
| Deployment bonus | C10 | Render URL |
| Demo video bonus | C10 | Loom/script |
| Auth/SSO/roles bonus | C3 | allauth-ready auth and RBAC tests |
| AI bonus | C7 | historical context only; not part of the current release |
| Creativity | C6, C8 | lexical search, seed corpus, provenance |
| Product quality | C1, C15, C18 equivalent sections | CI, tests, ADRs, runbook |
| Usability | C4, C5, C6, C14 equivalent sections | wireframes, accessibility, HTMX UI |

## 10. Architecture

### 10.1 C4 Context View

```text
Evaluator / Admin / Librarian / Member
        |
        v
Library Ops Web Application
        |
        +-- GitHub repository / CI
        +-- Render or equivalent Django host
        +-- PostgreSQL with lexical search indexes
        +-- Repo-local wireframes for design workflow
        +-- Open Library and Project Gutenberg metadata sources
```

### 10.2 C4 Container View

```text
Browser
  | HTML, CSS, HTMX requests
  v
Django Web App
  |-- Django templates and views
  |-- Django auth/allauth
  |-- service/selector/domain layers
  |-- management commands
  v
PostgreSQL
  |-- relational catalog/circulation data
  |-- lexical search indexes / tsvector data
```

### 10.3 C4 Component View

```text
catalog app
  models/forms/views/services/selectors
inventory app
  copy state and barcode management
circulation app
  checkout/return services and loan queries
search app
  exact search, FTS, facet filtering, deterministic ranking
audit app
  audit and provenance records
seed workflows
  accounts: demo roles and demo users
  catalog: public-domain import and provenance
  search: lexical refresh / rebuild helpers
```

### 10.4 Architectural Constraints

- The web layer MUST NOT implement business rules directly.
- Any auxiliary HTTP surface MUST preserve authorization and is not part of the current evaluator release path.
- Search relevance code SHOULD be deterministic and testable.
- Seed/import management commands MUST be idempotent.
- App must remain useful without optional external services.

## 11. Data Model

### 11.1 Core Entities

```text
BibliographicWork
- id
- title
- normalized_title
- original_publication_year
- description
- created_at
- updated_at
- archived_at

Contributor
- id
- display_name
- sort_name
- birth_year
- death_year
- external_ids

WorkContributor
- id
- work_id
- contributor_id
- role
- position

BookEdition
- id
- work_id
- title
- subtitle
- isbn10
- isbn13
- publisher
- publication_year
- language_code
- page_count
- description
- subjects
- external_ids
- cover_url
- uploaded_cover
- source_quality_score
- archived_at
- created_at
- updated_at

BookCopy
- id
- edition_id
- barcode
- status
- shelf_location
- condition_note
- acquired_at
- archived_at
- created_at
- updated_at

Loan
- id
- copy_id
- patron_id
- checked_out_by_id
- returned_by_id
- checked_out_at
- due_at
- returned_at

- Search is derived directly from `BibliographicWork`, `BookEdition`, `BookCopy`, and `Loan` records via query helpers and full-text indexes. No persisted `SearchDocument` projection exists in the current release scope.

AuditEvent
- id
- actor_id
- action
- entity_type
- entity_id
- before_json
- after_json
- created_at

ExternalSourceRecord
- id
- source_name
- source_identifier
- source_url
- license_note
- work_id
- edition_id
- imported_at
- fetched_at
```

### 11.2 Critical Invariants

- A copy has at most one active loan.
- A copy with an active loan is `ON_LOAN`.
- A copy without an active loan may be `AVAILABLE`, `MAINTENANCE`, `LOST`, or `ARCHIVED`.
- A returned loan has `returned_at` and `returned_by_id`.
- Archived records are excluded from public catalog results by default.
- Search availability is recomputed from copy/loan state, not generated by AI.

## 12. Lexical Search Design

Search ranking MUST use this priority order:

1. exact identifiers: ISBN-13, ISBN-10, barcode, Open Library ID, Gutenberg ID;
2. exact normalized title/contributor phrase;
3. PostgreSQL full-text search with weighted `tsvector`;
4. optional fuzzy/typo tolerance only if it stays lexical and does not outrank exact matches;
5. deterministic ranking and business boosts.

### 12.2 Baseline PostgreSQL FTS

Use weighted vectors:

- A: title, subtitle, exact contributor names;
- B: subjects, genres, tags, publisher;
- C: description;
- D: source/provenance text.

Queries should use safe PostgreSQL functions such as `websearch_to_tsquery` or `plainto_tsquery` rather than manually interpolating user input.

### 12.3 Lexical ranking and explanations

- Exact identifiers outrank full-text matches.
- Exact normalized title/contributor phrases outrank looser keyword matches.
- Availability boosts may improve ordering within the lexical tier but MUST not hide exact identifier matches.
- Result explanations should say why a record matched and which lexical signals contributed.

### 12.4 Search Quality Tests

| Query | Expected |
|---|---|
| `9780141439518` | exact ISBN result first |
| `OL7353617M` | Open Library ID result first if present |
| `barcode:COPY-0001` | copy context first |
| `austen pride prejudice` | title/contributor results above looser keyword-only matches |
| `books about social class and marriage` | relevant classics via lexical title/subject/description matches |
| `dystopian surveillance authoritarian` | relevant dystopia records if seeded |
| whitespace/case variants | same normalized intent |
| nonsense query | empty state, no crash |

### 12.5 Superseded AI metadata suggestions

AI metadata suggestions are out of scope for the current release. If a later release reintroduces them, they MUST be added through a new PRD update and a new Task Master slice rather than revived implicitly.

## 13. Seed Data and Demo Corpus

### 13.1 Seed and Import Commands

These management commands live in the owning apps. They do not imply a standalone `seed` package.

```bash
uv run python manage.py seed_roles
uv run python manage.py seed_demo_users --reset-passwords
uv run python manage.py import_public_domain_catalog --source=openlibrary --limit=1000 --dry-run
uv run python manage.py import_public_domain_catalog --source=openlibrary --limit=1000
uv run python manage.py seed_circulation_examples --refresh
```

### 13.2 Demo Credentials

These are disposable seeded accounts and may be documented in README:

```text
admin@libraryops.demo      / <local-demo-password-from-seed-command>
librarian@libraryops.demo  / <local-demo-password-from-seed-command>
member@libraryops.demo     / <local-demo-password-from-seed-command>
```

### 13.3 Source Policy

- Use Open Library dumps for bulk metadata rather than API scraping.
- Use Project Gutenberg metadata/catalogs for public-domain-oriented classics.
- Use Open Library cover URLs when available.
- Store provenance and license/copyright notes.
- Do not commit imported corpora, downloaded dumps, generated embeddings, or model caches.

### 13.4 Corpus Selection Heuristic

For a recognizable 1,000-record demo corpus, prefer records that have:

- English language metadata;
- recognized title and contributor;
- subject/description data;
- public-domain or older-work signal;
- external identifiers;
- cover image candidate;
- high source quality.

## 14. UX and Accessibility Workflow

### 14.1 Product Screens

The MVP UI includes:

- public landing page;
- login page;
- dashboard;
- catalog/search page;
- book detail page;
- create/edit book page;
- checkout modal/page;
- return/active loans page;
- member loans page;
- admin/user role page;
- evaluator help or release notes link if needed.

### 14.2 UX Principles

- Primary actions are role-aware.
- Empty states explain what to do next.
- Search result cards show title, contributors, availability, identifiers, and why matched.
- Destructive/archive actions require confirmation.
- Borrow/return wording is user-facing; checkin/checkout may be implementation terminology only.

### 14.3 Accessibility Requirements

- Every form field has a label.
- Focus order follows visual order.
- Keyboard users can complete catalog, checkout, and return flows.
- Error messages are associated with fields.
- Modals follow accessible dialog behavior.
- Color is not the only indication of status.

### 14.4 Wireframe Workflow

The repo includes `docs/design/wireframes.md` as the portable design source.
Implementation should proceed from that repo-local authority rather than from a
private design-tool workflow.

## 15. Agent System and MCP Workflow

### 15.1 Primary Agent Topology

- Coordinator: source-of-truth alignment and task sequencing.
- PRD architect: PRD and capability graph.
- Task Master governor: task graph and status.
- Spec Kit governor: constitution/spec consistency.
- Researcher: current docs and examples.
- Code-intelligence architect: RTK, code graph, symbol, AST, repo-pack, context, MCP, and tooling decisions.
- Implementer: one bounded task/subtask.
- Reviewer: correctness/security/traceability.
- Search architect: search and relevance.
- Seed data engineer: corpus/provenance.
- UX design architect: wireframes and design-to-template mapping.
- DevOps release manager: CI/CD/release/deploy.

### 15.2 MCPs

| MCP | Required? | Purpose |
|---|---:|---|
| Task Master | Yes | task graph, dependencies, task notes/status |
| Context7 | Yes | current version-specific library docs |
| Exa | Yes | current research/search beyond local docs |
| code-review-graph | Yes | structural map and blast-radius review context |
| Serena | Yes | symbol-level project context and refactor planning |

Code-intelligence tools are not all MCPs and are governed separately:

| Tool | Default status | Purpose |
|---|---|---|
| RTK | Required selected stack | compact noisy shell output while preserving raw evidence paths |
| code-review-graph | Required selected stack | structural map and blast-radius planning |
| Serena | Required selected stack | symbol-level semantic retrieval/refactor planning |
| ast-grep | Required selected stack | deterministic AST search and codemod planning |
| Repomix | Required selected stack with strict excludes | bounded repo context snapshots and token counts |
| tokenix / Headroom / LeanCTX | Benchmark candidates | broader context compression/indexing layers requiring local benchmark before adoption |
| cloud semantic-code stores | Deferred by default | semantic code search requiring credentials/cloud data movement |

### 15.3 Agent Work Rules

- Read constitution and relevant PRD section before editing.
- Run or inspect `task-master next` before implementing.
- Use the Socratic decision framework before material tooling, MCP, architecture, context-budget, cost, credential, or scope changes.
- Use RTK for noisy command output, but raw output/full logs for final evidence.
- Use code graph/symbol/AST/repo-pack tools only according to `AGENTS.md`, the relevant code-intelligence skill workflow, and the current docs hub surfaces.
- Use Context7 before using framework/library APIs that may have changed.
- Use Exa for current external research or examples.
- Do not store secrets in Task Master metadata, PRD, README, or MCP config.
- If the user explicitly asks for delegation, the coordinator MUST trust
  bounded subagent ownership, avoid duplicate local implementation in those
  owned slices, and prefer waiting or blocked status over taking work back
  early.
- Current meta-system hardening priority order is:
  1. source-of-truth alignment across constitution, PRD, tasks, AGENTS, and skills;
  2. required tool/runtime verification for Codex, Task Master, RTK, and selected code-intelligence surfaces;
  3. coordinator-first routing and bounded specialist ownership;
  4. continuation, evidence, and documentation integrity;
  5. focused governance/smoke tests that fail fast on meta-system regressions.

### 15.4 Connector Truthfulness

The repository configures Exa, Context7, Task Master, code-review-graph, and Serena MCPs, but configured access is not the
same as actual usage. Agents MUST record direct connector usage in Task Master notes or the evidence
register. If a connector is unavailable in a session, agents MUST say so and use available official sources.

### 15.5 MCP Configuration Rules

- Commit examples, not real secrets.
- Keep API keys in user-local config or environment variables.
- Use the custom Task Master MCP set
  `get_tasks,next_task,get_task,set_task_status,update_subtask,parse_prd` by
  default, and keep heavier analysis, expansion, and model-tuning operations on
  the pinned CLI.
- code-review-graph and Serena are selected project MCPs; new MCP servers beyond the selected stack require explicit user approval and local trust review.

## 16. CI/CD, Branching, and Release Governance

### 16.1 Branch Model

```text
main       production/release branch
development integration branch
feature/TM-<id>-<slug>  implementation branches
release/vX.Y.Z          optional release preparation
```

Remote repository policy MAY reinforce this branch flow, but it is not the
source of truth. If GitHub blocks a required merge, push, or release step, stop
and resolve the policy or user instruction instead of working around it.

### 16.2 Required Pull Request Evidence

Every PR must include:

- Task Master task ID;
- PRD capability/feature references;
- ADR references when decision-significant;
- tests added/updated;
- checks run;
- screenshots or demo evidence for UI changes;
- self-review statement.

### 16.3 Required CI Gates

- control-plane package hygiene check;
- format check;
- lint;
- type check;
- import architecture check when Django package exists;
- Django system checks when bootstrap exists;
- migration drift check when bootstrap exists;
- pytest suite;
- property tests;
- commitlint;
- dependency/security scan where practical;
- build/static asset check.

### 16.4 Release Policy

- Conventional Commits drive SemVer.
- `feat` implies minor version change.
- `fix` implies patch version change.
- breaking changes require `!` or `BREAKING CHANGE` footer.
- Releases are tagged from `main` only.
- Deployment commit must correspond to a release or documented pre-release.

## 17. Security and Privacy

### 17.1 RBAC Matrix

| Capability | Anonymous | Member | Librarian | Admin |
|---|---:|---:|---:|---:|
| View public catalog | Yes | Yes | Yes | Yes |
| Search catalog | Yes | Yes | Yes | Yes |
| View own loans | No | Yes | Yes | Yes |
| View all loans | No | No | Yes | Yes |
| Create/edit/archive catalog | No | No | Yes | Yes |
| Add/archive copies | No | No | Yes | Yes |
| Checkout/return | No | No | Yes | Yes |
| Manage roles/users | No | No | No | Yes |
| View audit log | No | No | Optional | Yes |
| Run seed/import commands | No | No | No | Local/admin only |

### 17.2 Security Controls

- CSRF protection enabled for forms.
- Server-side authorization for all privileged mutations.
- SQL injection avoided through ORM/query parameterization.
- File uploads validate type, extension, size, and image decode.
- Production settings enforce secure secret handling.
- Debug mode disabled in production.
- Demo credentials are disposable and resettable.
- AI outputs are reviewed before persistence.

### 17.3 Privacy Scope

This is a demo product. It should not store real patron data. Demo users and loan records are synthetic.

## 18. Verification Strategy

### 18.1 Kind-First Test Topology

```text
tests/control_plane/   agent workflow, governance, hooks, docs/process gates
tests/smoke/           deterministic bootstrap and environment checks
tests/unit/            isolated rules, normalization, serializers/forms/helpers
tests/integration/     services, views, APIs, DB constraints, management commands
tests/property/        invariant-heavy generated input/state transitions
tests/e2e/             evaluator-visible browser and navigation flows
```

Coverage still follows a pyramid shape inside that topology: control-plane and smoke checks fail fast, unit/property
coverage protects invariants, integration tests cover orchestration, and E2E tests stay few and high-signal. Temporary
domain folders are migration waypoints only and should converge into the kind-first layout above.

### 18.2 Unit and Integration Tests

- ISBN normalization and validation.
- Permission decisions.
- Catalog form validation.
- Copy status transitions.
- Checkout/return services.
- Search normalization.
- Rank fusion.
- App-owned URL/view/template flows and redirect/403 behavior.

### 18.3 Property-Based Tests

- Generated circulation sequences never create duplicate active loans.
- Return without active loan fails.
- Checkout unavailable copy fails.
- Copy status and active loan state remain consistent.
- Search normalization is idempotent.
- ISBN normalization preserves valid identities and rejects invalid checksums.

### 18.4 E2E Tests

- Librarian can create/edit/archive a catalog record.
- Librarian can checkout and return a copy.
- Member cannot see mutation actions and direct mutation fails.
- Search exact ISBN ranks first.
- Semantic search returns stored records when embeddings exist.

### 18.5 Accessibility Tests

Automated tests MAY use axe or Playwright assertions. Manual review must check:

- keyboard navigation;
- visible focus states;
- labels and errors;
- modal focus trap/return;
- status indicators not color-only.

## 19. Acceptance Criteria

### 19.1 Catalog CRUD

```gherkin
Scenario: Librarian creates a catalog record
  Given I am signed in as a Librarian
  When I create a work, edition, and copy with required metadata
  Then the catalog shows the record
  And the record has at least one available copy
  And an audit event is recorded
```

### 19.2 RBAC

```gherkin
Scenario: Member cannot mutate catalog
  Given I am signed in as a Member
  When I attempt to create a catalog record by direct POST
  Then the request is rejected
  And no catalog record is created
```

### 19.3 Borrow

```gherkin
Scenario: Librarian borrows an available copy to a member
  Given a copy is available
  And I am signed in as a Librarian
  When I checkout the copy to a Member
  Then an active loan exists
  And the copy is on loan
  And the copy cannot be checked out again
```

### 19.4 Return

```gherkin
Scenario: Librarian returns an active loan
  Given a copy is on loan
  And I am signed in as a Librarian
  When I return the copy
  Then the loan has a returned timestamp
  And the copy is available
```

### 19.5 Search

```gherkin
Scenario: Exact ISBN outranks semantic match
  Given the catalog contains a book with ISBN "9780141439518"
  When I search for "9780141439518"
  Then that exact edition is the first result
  And the result explanation includes "ISBN exact match"
```

### 19.6 Seed Refresh

```gherkin
Scenario: Demo seed can be refreshed
  Given I run the demo seed command with refresh enabled
  When the command completes
  Then the demo users exist
  And the catalog has seeded records with provenance
  And imported corpora are not committed to git
```

## 20. Decision Register

The standalone ADR set is consolidated so humans and agents can navigate consequential decisions without treating every small policy note as an ADR. Detailed entries live in `docs/adr/`.

| ADR | Decision | Status |
|---|---|---|
| ADR-0001 | Source of truth and planning model: PRD + Spec Kit + Task Master + ADR/supporting docs. | Accepted |
| ADR-0002 | Application architecture: C4 views, arc42 quality/risk framing, pragmatic domain boundaries, Django service/selector layering. | Accepted |
| ADR-0003 | Search, AI assistance, and data provenance: exact + FTS + vector baseline, AI suggestions reviewed, deterministic seed import. | Accepted |
| ADR-0004 | Agent toolchain, MCP, and context optimization: required Codex/RTK/code-review-graph/Serena/ast-grep/Repomix stack. | Accepted |
| ADR-0005 | Delivery, quality, security, and release governance: CI, branches, quality gates, security, release, deployment. | Accepted |
| ADR-0006 | Design and UX workflow: repo-local wireframes as the design authority. | Accepted |
| ADR-0007 | Agent skills and meta-system governance: skills, hooks, context, and tool access are validated implementation surface. | Accepted |

## 21. Risk Register

| Risk | Impact | Likelihood | Mitigation | Fallback |
|---|---:|---:|---|---|
| PRD too broad for available time | High | Medium | Prioritize P0/P1; Task Master dependencies | Cut AI metadata suggestions |
| Agent drift from task graph | High | Medium | Constitution + AGENTS + Task Master workflow | Stop and re-plan |
| Blind MCP/tool adoption | High | Medium | Socratic decision gates + alternatives register | Ask user before new trust/cost/scope changes |
| Filtered command output hides failure detail | Medium | Medium | RTK/raw evidence policy + tee/raw reruns | Rerun raw commands |
| Code graph output treated as proof | Medium | Medium | Source/test inspection required after graph findings | Fall back to raw source review |
| Django bootstrap conflicts with strict Pyright | Medium | Medium | Type pure modules strictly; document pragmatic suppressions | Relax dynamic Django files only |
| Evaluator UI drifts into a monolithic shared web layer | Medium | Medium | App-owned URL/view/template rules plus review | Split routes/views/templates by app before adding more flows |
| Search overengineered | Medium | Medium | Baseline exact + FTS first | Keep the release scope lexical-only |
| ParadeDB unavailable on deployment | Low | High | Optional adapter only | Use standard FTS |
| Public data licensing confusion | Medium | Medium | Store provenance and license notes; use official dumps/catalogs | Use synthetic seed records |
| Free hosting limits | Medium | Medium | Keep corpus small; document local fallback | Provide local demo only if needed |
| File upload security | Medium | Medium | Validate size/type/decode; limit uploads | External cover URLs only |
| CI ignores real failures while bootstrap incomplete | High | Medium | Conditional gates that become strict once files exist | Manual checklist until bootstrap exists |
| Test topology migration stalls in temporary domain folders | Medium | Medium | Kind-first placement rules and governance tests | Finish the split before broadening coverage further |

## 22. Task Master Parsing Contract

Task Master should parse this PRD as follows:

1. `### Capability:` headings become top-level tasks.
2. `#### Feature:` headings become subtasks under the nearest capability.
3. `**Depends on:** [...]` lines provide dependency hints.
4. Acceptance criteria and test strategy become implementation/test context.
5. Development phases define priority and sequencing.
6. Decision register entries provide ADR context.
7. Source register informs research mode and external citation grounding.

Recommended commands:

```bash
task-master parse-prd .taskmaster/docs/prd.md --research
task-master analyze-complexity --research
task-master complexity-report
task-master expand --all --research
task-master validate-dependencies
task-master list
task-master next
```

After task generation, review generated tasks manually. If tasks are too broad, update this PRD or use
`task-master expand --id=<id> --research` with a narrow prompt.

## 23. Source Register

The following sources informed this PRD. They should be rechecked by the implementation agent with Context7,
Exa, or web research before making version-sensitive implementation changes.

| ID | Source | Use |
|---|---|---|
| S01 | Task Master RPG template: https://raw.githubusercontent.com/eyaltoledano/claude-task-master/main/.taskmaster/templates/example_prd_rpg.md | PRD structure and parsing contract. |
| S02 | Task Master docs: https://docs.task-master.dev/capabilities/task-structure | Task fields, dependencies, metadata, best practices. |
| S03 | Spec Kit quickstart: https://github.github.com/spec-kit/quickstart.html | Constitution/spec/plan/tasks workflow. |
| S04 | Django 5.2 auth docs: https://docs.djangoproject.com/en/5.2/topics/auth/ and Django download/support matrix: https://www.djangoproject.com/download/ | Users, groups, permissions, sessions, and LTS baseline. |
| S05 | Django docs: https://docs.djangoproject.com/ and HTMX docs: https://htmx.org/docs/ | Server-rendered Django and HTMX references. |
| S06 | HTMX docs: https://htmx.org/ | Hypermedia interactions without large frontend framework. |
| S07 | django-htmx docs: https://django-htmx.readthedocs.io/ | Django integration with HTMX. |
| S08 | PostgreSQL FTS docs: https://www.postgresql.org/docs/current/textsearch-controls.html | `tsvector`, `tsquery`, ranking. |
| S09 | Django ORM query docs: https://docs.djangoproject.com/en/5.2/topics/db/queries/ | Query composition for lexical search helpers. |
| S10 | PostgreSQL indexes docs: https://www.postgresql.org/docs/current/indexes.html | Search and filter indexing strategy. |
| S11 | PostgreSQL query planner docs: https://www.postgresql.org/docs/current/using-explain.html | Explain plans for search performance checks. |
| S12 | Library of Congress BIBFRAME model: https://www.loc.gov/bibframe/docs/bibframe2-model.html | Work/Instance/Item domain inspiration. |
| S13 | Library of Congress MARC 21: https://www.loc.gov/marc/bibliographic/ | Bibliographic metadata context. |
| S14 | Dublin Core DCMI Terms: https://www.dublincore.org/specifications/dublin-core/dcmi-terms/ | Simple metadata terms. |
| S15 | Open Library data/API/covers: https://openlibrary.org/developers/dumps and https://openlibrary.org/dev/docs/api/covers | Bulk metadata and cover URLs. |
| S16 | Project Gutenberg: https://www.gutenberg.org/ and https://www.gutenberg.org/ebooks/offline_catalogs.html | Public-domain-oriented corpus and metadata catalogs. |
| S17 | Hypothesis docs: https://hypothesis.readthedocs.io/ | Property-based tests. |
| S18 | Pyright docs: https://microsoft.github.io/pyright/ | Static type checking. |
| S19 | Ruff docs: https://docs.astral.sh/ruff/ | Linting and formatting. |
| S20 | Import Linter docs: https://import-linter.readthedocs.io/ | Architecture import constraints. |
| S21 | Render Django docs: https://render.com/docs/deploy-django | Deployment path. |
| S22 | GitHub pull request docs: https://docs.github.com/pull-requests | Pull request flow and review mechanics. |
| S24 | Context7 docs: https://github.com/upstash/context7 and Exa MCP docs: https://exa.ai/docs/reference/exa-mcp | Agent research/documentation MCPs. |
| S25 | WCAG overview: https://www.w3.org/WAI/standards-guidelines/wcag/ | Accessibility baseline. |
| S26 | OWASP ASVS/SAMM: https://owasp.org/www-project-application-security-verification-standard/ and https://owaspsamm.org/ | Security verification and SDLC framing. |
| S27 | C4 model: https://c4model.com/ | Architecture communication. |
| S28 | RFC 2119/8174: https://datatracker.ietf.org/doc/html/rfc2119 and https://www.rfc-editor.org/rfc/rfc8174.html | Normative requirement language. |
| S29 | django-allauth docs: https://docs.allauth.org/ | OAuth/social auth readiness. |
| S30 | Playwright docs: https://playwright.dev/ | Browser E2E testing. |
| S31 | OpenAI Codex MCP docs: https://developers.openai.com/codex/mcp | Codex MCP configuration and connector setup. |
| S32 | OpenAI Codex config/models docs: https://developers.openai.com/codex/config and https://developers.openai.com/codex/models | Project-scoped config and model selection. |
| S34 | GitHub Actions docs: https://docs.github.com/actions | CI/CD workflow automation. |
| S35 | Conventional Commits: https://www.conventionalcommits.org/en/v1.0.0/ | Commit structure and release automation alignment. |

## 24. Verification Addendum: Tooling, Deployment, and Evidence

### 24.1 Current Artifact Review Status

The current archive has been reviewed as a **governed control-plane package bootstrap**. It contains PRD, constitution,
agent configuration, ADRs, CI bootstraping, runbook, and wireframes. It does not yet contain the completed
Django application. The PRD and agent instructions MUST therefore describe the app as planned, not as
already implemented.

A personal-context lookup during the 2026-06-12 review returned no additional relevant memory. The review
therefore used the current conversation, original control-plane package archive, updated control-plane package archive, and current
primary-source research.

### 24.2 Context Preservation Checks

The updated control-plane package preserved the prior strategic decisions:

- simplified Python/Django product scope;
- Spec Kit for governance;
- Task Master RPG PRD for execution planning;
- Codex as the primary agent with MCP-compatible configuration;
- consolidated documentation rather than many competing docs;
- Work/Edition/Copy/Loan domain model;
- Borrow/Return terminology for check-in/check-out ambiguity;
- exact-identifier-first lexical search;
- deterministic seed-data management commands;
- reviewed-PR, CI, Conventional Commits, and SemVer workflow.

The updated control-plane package added repo-local wireframes, UX design skill/agent, runbook, deterministic-seed ADR,
evidence register, and context-drift review. It removed committed `.pytest_cache` artifacts.

### 24.3 Connector Verification Policy

Exa, Context7, and Task Master MCP are intended implementation tools, but claims about their use
must be evidence-based. During implementation:

- Context7 SHOULD be used for version-specific framework/API documentation.
- Exa SHOULD be used for broad current research and ecosystem examples.
- Task Master MCP/CLI MUST be used for task graph execution in implementation environments.
- Any direct connector usage SHOULD be recorded in Task Master notes, the PRD source register, or an ADR when the decision is durable.

If a review session lacks direct connector access, the agent MUST say so rather than imply usage.

### 24.4 Selected Tooling Matrix

| Category | Baseline choice | Why | Alternatives / constraints |
|---|---|---|---|
| Product framework | Django 5.2 LTS | Auth, admin, ORM, migrations, forms, management commands, long support window | Django 6.x later; FastAPI only if the project pivots away from the current server-rendered scope |
| Interface | Django templates + HTMX | Server-rendered first-party UI without a dedicated API layer | DRF only if the scope ever expands to a public REST API |
| UI | Django templates + HTMX | Low-code, server-driven UI with good demo velocity | React/Next.js only if frontend complexity grows |
| Planning | Task Master RPG PRD | Explicit dependencies and parseable task graph | Standard PRD for smaller projects |
| Governance | Spec Kit constitution | Enforceable principles before implementation | Plain ADRs alone are less process-oriented |
| Agent | Codex with MCP config | Repo-local agent config and MCP-capable workflow | Claude Code/Cursor/Windsurf should remain compatible |
| Research | Context7 + Exa | Versioned docs plus broader current research | Official web research fallback when connectors unavailable |
| Design | Repo wireframes | Portable source and implementation authority | Private design-tool state must not become the only source |
| Search | Exact IDs + Postgres FTS | Correct library identifier behavior plus deterministic lexical discovery | Optional adapters are out of current scope |
| Seed data | Django management commands | Reproducible, refreshable, auditable seed process | Fixtures only for tests/small examples |
| Command-output optimization | RTK | User-accepted optimization for noisy shell output | Raw reruns/full logs remain required for evidence |
| Code intelligence | code-review-graph + Serena + ast-grep + bounded Repomix | Graph, symbol, AST, and context packaging without replacing source review | New MCPs/broad context layers require approval |
| Decisioning | Socratic decision framework | Prevents guessing and unexamined tool adoption | Pause and ask for trust/cost/scope decisions |
| Quality | Ruff, Pyright, Import Linter, pytest, Hypothesis, Playwright | Static, architectural, unit/property/E2E coverage | Tighten gradually after bootstrap exists |
| Deployment | Render + managed PostgreSQL | Familiar Django deployment path with a small operational surface | Fly/Railway/Heroku/container host if Render limits apply |
| SDLC | GitHub Actions + reviewed PR branch flow + Conventional Commits + SemVer | Visible, enforceable solo-project governance | Merge queue optional and likely excessive for solo demo |

### 24.5 Documentation Evidence Package

A release is not evaluator-ready until the repo can show:

- README with live URL, demo credentials, local setup, feature checklist, and known limitations;
- PRD with capability tree, acceptance criteria, decisions, and source register;
- constitution with enforceable project rules;
- AGENTS instructions for repeatable agent work;
- research register showing material evidence and assumptions;
- context-drift review for major revisions;
- runbook for local setup, deployment, seed refresh, smoke tests, and rollback;
- wireframes or implementation screenshots for key flows;
- PR-attached screenshots and validation artifacts for key evaluator-visible flows;
- CI results and test commands;
- release tag and changelog when release automation exists.

### 24.6 Deployment Completeness Requirements

Deployment work MUST cover application hosting and operational evidence:

1. production Django settings;
2. managed PostgreSQL connection with a deterministic migration path appropriate to host constraints;
3. search index and full-text ranking configuration appropriate to the release scope;
4. static files through WhiteNoise or host-supported equivalent;
5. media upload strategy for book covers;
6. environment variables without committed secrets;
7. deterministic production demo seed command;
8. health endpoint;
9. smoke-test checklist;
10. README update with live URL and demo accounts;
11. release tag and rollback/reset notes.

### 24.7 Claim Status

As of this PRD revision:

- **Verified:** standards/tooling/deployment claims recorded in the source register and research register.
- **Mechanically verified:** control-plane package archive hygiene and Markdown/Python static checks.
- **Planned but not implemented:** app-based Django UI slices, database models, search services, kind-first test end state, seed importers, API, and deployment.
- **Implementation-time checks required:** selected PostgreSQL host extension support, ParadeDB availability, final Codex model availability/cost policy, strict required-tooling check, and actual Task Master-generated task graph quality.
