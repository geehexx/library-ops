---
name: search-design
description: Use when designing exact search, PostgreSQL full-text search, pgvector, BM25, ranking, or search tests.
---

# Search Design Skill

## Ranking discipline

1. Exact ISBN/barcode/external ID.
2. Exact title/author phrase.
3. PostgreSQL `tsvector` full-text.
4. Optional ParadeDB/BM25 adapter.
5. pgvector semantic search.
6. Reciprocal rank fusion and business boosts.

## Rules

- Availability comes from database state only.
- Semantic search never overrides exact identifiers.
- Result explanation must disclose ranking sources.
- Add tests for exact, keyword, subject, semantic, and empty queries.

## Output

- Search design/update:
- Ranking impact:
- Data/model impact:
- Tests required:
- ADR impact:
