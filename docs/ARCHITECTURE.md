---
id: DOC-ARCHITECTURE
title: Architecture Approach, Alternatives, and Validation
status: active
last_reviewed: 2026-06-17
related_prd: ../.taskmaster/docs/prd.md
related_adrs:
  - ../adr/0002-application-architecture-and-domain-boundaries.md
  - ../adr/0004-agent-toolchain-mcp-and-context-optimization.md
---

# Architecture Approach, Alternatives, and Validation

This is the canonical architecture explainer. Operational commands live in
`../SETUP.md`; agent-operating rules live in `../AGENTS.md`, and
documentation-local decisioning guidance lives in `AGENTS.md` rather than being
duplicated here.

## Decision summary

The project uses a **hybrid architecture communication model**:

1. **C4-style views** for fast orientation: system context, containers,
   components, and code-level diagrams only when they clarify implementation.
2. **arc42-style quality and risk framing** for measurable quality attributes,
   cross-cutting concerns, runtime/deployment views, and risks.
3. **Pragmatic domain modeling** rather than full enterprise DDD. Domain
   language is explicit, bounded contexts are named, and invariants live in
   services/domain functions, but the implementation remains idiomatic Django.
4. **Import Linter + tests** as executable architectural validation.

This is not unexamined C4 or unexamined DDD. C4 alone is too diagram-centric
for delivery governance; arc42 alone is too documentation-heavy for a small
interview project; full DDD is too much ceremony for a Django demo; an anemic
CRUD-only design would miss circulation/search invariants. The selected hybrid
keeps the architectural intent visible without creating a second application
framework inside Django.

## Alternatives examined

| Alternative | Strength | Counterfactual evidence / weakness | Decision |
|---|---|---|---|
| Pure C4 | Excellent shared mental model and progressive diagram depth. | Does not by itself specify quality gates, decision governance, or runtime validation. | Use C4 views as the architecture map, not the whole process. |
| Pure arc42 | Strong coverage of quality goals, risks, constraints, runtime/deployment, and decisions. | Heavier template; too much root documentation would obscure the PRD and task graph. | Use arc42 ideas for quality/risk/runtime docs, not the entire template. |
| Full strategic/tactical DDD | Rich ubiquitous language, aggregates, bounded contexts, domain services. | Overkill for small Django demo; repository abstractions and deep aggregate layering can fight Django ORM idioms. | Use pragmatic bounded contexts and invariants only. |
| Clean Architecture / Hexagonal | Clear dependency inversion and ports/adapters. | Can produce redundant adapters around Django ORM/templates; unnecessary for most local flows. | Use the dependency rule selectively at integration boundaries. |
| Rails/Django conventional CRUD | Fastest to implement. | Weak for loan invariants, search ranking provenance, seed provenance, and role-based access evidence. | Use idiomatic Django, but with service/selector boundaries. |
| Microservices / event-driven | Clear bounded deployment for large systems. | Grossly disproportionate; hurts demo speed, testing, and deployment. | Rejected. |
| Event sourcing / CQRS | Strong auditability and read-model separation. | Excessive complexity; audit trail can be implemented with ordinary append-only audit records. | Rejected for MVP; revisit only for explicit event-history feature. |

## Architecture view set

### C1: System context

```text
Evaluator / Admin / Librarian / Member
        |
        v
Library Ops web application
        |
        +-- PostgreSQL
        +-- optional external metadata sources for public-domain import
        +-- GitHub Actions / Render for delivery
```

### C2: Containers

```text
Browser
  -> Django web + HTMX templates
  -> PostgreSQL
  -> background/management commands for seed import and search refresh
  -> CI/CD and deployment runtime
```

### C3: Components

```text
accounts        roles, permissions, demo users
catalog         works, editions, contributors, subjects, cover metadata
inventory       physical/digital copies and availability projection
circulation     checkout, return, renewal, loan invariants
audit           append-only user/action evidence
search          exact identifier search, lexical ranking, result explanations
web             templates, HTMX endpoints, and request/response orchestration
```

### C4/code-level guidance

Only add class/function-level diagrams when they remove ambiguity for:

- circulation state transitions;
- search ranking/fusion flow;
- import provenance flow;
- authorization boundary for an evaluator-critical action.

Do not create code-level diagrams for routine Django views, forms, or admin
registration.

## Pragmatic domain model

The bounded contexts are implementation modules, not distributed services.
Cross-context communication stays in-process and transactional unless a future
decision changes deployment topology.

| Context | Owns | Must not own |
|---|---|---|
| `accounts` | users, roles, permission helpers | loan state, catalog metadata |
| `catalog` | work/edition/contributor/subject metadata | copy availability, active loans |
| `inventory` | copies, copy status, location, availability projection | member borrowing rules |
| `circulation` | loan workflow, transactional checkout/return/renewal | search ranking, metadata import |
| `search` | exact identifiers, lexical ranking, filters, explanations | loan mutation |
| `audit` | append-only evidence | primary business state |

## Django layer contract

| Layer | Responsibility | Prohibited |
|---|---|---|
| `models.py` | schema, constraints, relationships, simple model methods | request/user orchestration, broad business workflows |
| `domain.py` | pure calculations and state-transition guards | ORM writes, external IO |
| `services.py` | transactional writes and workflow invariants | template rendering, HTTP response construction |
| `selectors.py` | read/query access and projection assembly | state mutation |
| `forms.py` | request/form validation for template flows | business mutations outside services |
| `views.py` | request/response orchestration | direct circulation/catalog state mutation |
| `tasks.py` / management commands | batch/import/search-refresh orchestration | hidden schema changes or non-idempotent seed writes |
| `tests/` | executable behavior and architecture evidence | brittle tests coupled to irrelevant internals |

## Validation model

Architecture is considered valid only when prose, generated tasks, source
layout, and the canonical gates agree.
Use `docs/process/quality-gates.md` for the exact command ladder.

The sandbox profile may be used only when the execution environment cannot
install the required local tools. It is a constrained-environment waiver, not a
project policy.

## Testing strategy derived from the architecture

| Concern | Primary test type | Examples |
|---|---|---|
| Domain invariants | unit/property | checkout cannot create duplicate active loans; return is idempotent only where specified |
| Transactions | integration | concurrent checkout races; copy state and loan state commit/rollback together |
| Authorization | integration/E2E | member cannot manage catalog; librarian can checkout/return; admin can manage users |
| Search ranking | unit/integration/property | exact ISBN wins; subject search finds seeded works; keyword ranking remains explainable |
| Seed import | unit/integration | provenance captured; `--limit` respected; refresh is idempotent |
| UI contract | integration/schema | Server-rendered forms and views match PRD acceptance examples |
| UI flows | Playwright | login, add book, search, checkout, return, role boundary |
| Meta-system | config/CI | Codex config, skills, MCP/toolchain, ADR/index, and direct validation gates |

## Architecture smell list

Stop and correct the design if any of these appear:

- views mutate loan/catalog state directly instead of calling services;
- selectors import views/forms/response modules;
- search writes authoritative catalog state;
- AI suggestion output is applied without provenance and human review;
- seed commands require private credentials for the demo path;
- generated corpora, embeddings, media, caches, or local MCP state enter git;
- ADRs are used for routine facts rather than consequential decisions;
- Task Master and Spec Kit diverge without a reconciliation note.
