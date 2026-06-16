# ADR-0003: Search, AI assistance, and data provenance

- Status: accepted
- Date: 2026-06-13
- Deciders: user, project coordinator
- Supersedes: ADR-0005, ADR-0010, ADR-0011

## Context

The demo must showcase library search and AI-assisted metadata without hiding data quality or provenance. Search must work with exact identifiers, human search terms, and semantic queries, while availability remains database-derived.

## Decision

Use a hybrid search baseline:

1. Exact identifiers and barcodes outrank all fuzzy/semantic results.
2. PostgreSQL full-text search is the baseline keyword path.
3. pgvector is additive for semantic similarity.
4. ParadeDB/BM25 remains behind an adapter until the implementation environment confirms extension support and ranking benefit.
5. AI metadata assistance may suggest summaries, subjects, or tags, but generated fields must be marked as AI-assisted and reversible.
6. Demo data comes from deterministic Django management commands with provenance, license notes, idempotency, `--dry-run`, `--limit`, and safe refresh behavior.

## Alternatives considered

| Alternative | Benefit | Rejected or adapted because |
|---|---|---|
| Vector-only search | Impressive AI demo | Poor exact-match behavior and weak explainability for library records. |
| PostgreSQL FTS only | Simple and portable | Misses semantic discovery and AI showcase value. |
| Mandatory ParadeDB | Better BM25 ranking | Adds deployment risk; use adapter until environment support is proven. |
| Static fixtures only | Small review surface | Too rigid and weak on provenance/rebuild. |
| Live external imports at runtime | Fresh data | Demo reliability and rate/license risks. |

## Consequences

- Search quality is measurable and explainable.
- Availability and circulation state remain authoritative database facts.
- Seed data can be regenerated without committing bulk public-domain corpora.

## Validation

- Ranking tests cover exact, FTS, semantic, and blended queries.
- Property tests cover normalization and availability invariants.
- Seed commands record provenance and support dry runs.
