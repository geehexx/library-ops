# Application code agent rules

- Follow pragmatic Django layering: models, domain helpers, services, selectors, forms, views/API, tasks, tests.
- Preserve Import Linter boundaries.
- Use Serena and code-review-graph before cross-context refactors.
- Raise an Escalation packet for ambiguous invariants, irreversible migrations, or low-confidence changes.
