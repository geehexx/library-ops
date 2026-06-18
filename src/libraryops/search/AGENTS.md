# Search subsystem rules

- Exact identifiers outrank fuzzy or semantic retrieval.
- ISBN, barcode, Open Library ID, and Gutenberg ID are identifier searches.
- PostgreSQL `tsvector` is the baseline keyword engine.
- pgvector semantic search is additive only.
- Availability must be database-derived.
- Every search change requires ranking tests.
