# Application code agent rules

- Follow pragmatic Django layering: models, domain helpers, services, selectors, forms, views, tasks, tests.
- Preserve Import Linter boundaries.
- Use Serena and code-review-graph before cross-context refactors.
- Keep non-obvious normalization or checksum helpers small, commented, and
  library-backed when a mature package can replace hand-rolled logic.
- Keep source functions small enough to satisfy `npm run python:lint`, which
  bundles Ruff format/check, source complexity, and docstring linting.
- When a Django module becomes a behavior cluster instead of a single unit,
  split it into a package and re-export the public surface with `__all__`.
- If model files become manager-heavy, move the managers into `managers.py`
  and keep the model declarations readable.
- Raise an Escalation packet for ambiguous invariants, irreversible migrations, or low-confidence changes.
