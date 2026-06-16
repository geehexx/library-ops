# ADR-0002: Application architecture and domain boundaries

- Status: accepted
- Date: 2026-06-13
- Deciders: user, project coordinator
- Supersedes: ADR-0004, ADR-0013, ADR-0018

## Context

The app is a small but non-trivial library operations system. It needs visible architectural judgment for interview review, but it must remain idiomatic Django and deliverable. The earlier decision said “C4 and DDD” without enough counterfactual analysis.

## Decision

Use a hybrid documentation and implementation model:

- C4 for visual architecture communication at System Context, Container, and Component levels.
- arc42-inspired sections for quality requirements, risks, cross-cutting concepts, and architectural decisions.
- Pragmatic domain modeling, not enterprise DDD: use bounded-context vocabulary where it clarifies invariants, but avoid repository abstractions and ceremony unless a real volatility boundary appears.
- Django 5.2 LTS baseline with server-rendered Django templates plus HTMX where useful.
- Service/selector layering: models hold persistence and local invariants; services own transactional writes; selectors own read/query composition; views/templates/API orchestrate; tasks/integrations own side effects.
- Import Linter contracts enforce allowed dependencies once the package exists.

Core domain split:

| Context | Main responsibility | Boundary risk |
|---|---|---|
| Catalog | Works, editions, authors, subjects, identifiers | Collapsing editions/copies into a single book record. |
| Inventory | Physical/digital copies, barcodes, availability state | Treating availability as a manually edited flag. |
| Circulation | Holds, loans, renewals, returns, fines/fees if added | State transitions bypassing transactional services. |
| Search | Exact/FTS/vector/BM25 ranking and facets | Vector-only or availability-unaware results. |
| Accounts | Staff/member roles and demo auth | Client-side or template-only authorization. |
| Audit | Important user/admin/system events | Missing traceability for circulation and AI actions. |
| Seed/import | Reproducible demo data and provenance | Unlicensed or non-reproducible imported records. |

## Alternatives considered

| Alternative | Benefit | Rejected or adapted because |
|---|---|---|
| Flat Django app | Fastest start | Blurs catalog/inventory/circulation invariants and makes agent edits risky. |
| Full enterprise DDD | Strong boundaries | Too much ceremony for the assignment; Django already provides useful infrastructure. |
| Transaction Script only | Simple and explicit | Works for thin flows but becomes brittle for circulation/search invariants. |
| Clean Architecture everywhere | Testable and explicit | Adds adapters/repositories that are not needed for most Django code. |
| Microservices | Strong service boundaries | Operationally unjustified and harmful for a small demo. |
| React/Next.js frontend | Modern SPA path | Not required; increases scope and splits attention from core library behavior. |
| arc42 only | Rich architecture template | Less immediately legible than C4 for reviewers; retained for qualities/risks/decisions. |

## Consequences

- The project can truthfully say it uses C4-style views and pragmatic DDD vocabulary without overclaiming full DDD.
- Implementation agents have concrete import/layer rules.
- Diagrams remain communication aids; tests and Import Linter are the enforcement mechanism.

## Validation

- `docs/architecture/architecture-approach.md` defines the hybrid model and boundary rules.
- `pyproject.toml` includes Import Linter contracts.
- Services/selectors/tests must be added with implementation tasks.
- Reviewers must reject direct state mutation from views/API when a service boundary exists.
