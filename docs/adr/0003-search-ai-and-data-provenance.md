# ADR-0003: Search scope and data provenance

- Status: superseded
- Date: 2026-06-13
- Deciders: Andrew Crozier

## Context

An earlier planning pass assumed the demo would showcase hybrid search and AI-assisted metadata. The current release has been intentionally narrowed to exact identifiers, PostgreSQL full-text search, and deterministic provenance-backed seed/import flows. This ADR remains as historical context and is superseded by the current PRD and task graph.

## Decision

The current release uses a lexical search baseline:

1. Exact identifiers and barcodes outrank all other results.
2. PostgreSQL full-text search is the baseline keyword path.
3. ParadeDB/BM25, semantic/vector search, and AI metadata assistance are out of the current release scope.
4. Demo data comes from deterministic Django management commands with provenance, license notes, idempotency, `--dry-run`, `--limit`, and safe refresh behavior.

## Alternatives considered

| Alternative | Benefit | Rejected or adapted because |
|---|---|---|
| Vector-only search | Impressive AI demo | Poor exact-match behavior, more deployment risk, and out of current release scope. |
| PostgreSQL FTS only | Simple and portable | Accepted for the current release because it keeps ranking deterministic and deployable. |
| Mandatory ParadeDB | Better BM25 ranking | Adds deployment risk and is not required for the current release. |
| Static fixtures only | Small review surface | Too rigid and weak on provenance/rebuild. |
| Live external imports at runtime | Fresh data | Demo reliability and rate/license risks. |

## Consequences

- Search quality is measurable and explainable without semantic/vector dependencies.
- Availability and circulation state remain authoritative database facts.
- Seed data can be regenerated without committing bulk public-domain corpora.

## Validation

- Ranking tests cover exact identifiers, keyword/FTS behavior, and explainable lexical matches.
- Property tests cover normalization and availability invariants.
- Seed commands record provenance and support dry runs.
