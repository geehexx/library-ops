---
name: search-design
description: Use when designing exact search, PostgreSQL full-text search, lexical ranking, or search tests.
---

# Search Design Skill

## Ranking discipline

1. Exact ISBN/barcode/external ID.
2. Exact title/author phrase.
3. PostgreSQL `tsvector` full-text.
4. Deterministic business boosts and tie ordering.

## Rules

- Availability comes from database state only.
- Semantic/vector search is out of the current release scope.
- Result explanation must disclose ranking sources.
- Add tests for exact, phrase, keyword, subject, facet, availability, and empty queries.

## Output

- Search design/update:
- Ranking impact:
- Data/model impact:
- Tests required:
- ADR impact:
