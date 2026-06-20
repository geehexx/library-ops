---
name: seed-data
description: Use when implementing demo users, public-domain corpus import, metadata provenance, image handling, or seed refresh commands.
---

# Seed Data Skill

## Rules

- Prefer Django management commands over static fixtures for demo seed data.
- Commands must support `--dry-run`, `--limit`, and safe `--refresh` behavior.
- Store source provenance for imported metadata.
- Keep imported corpora and model caches out of git.
- Demo credentials may be documented only for disposable seed users.

## Output

- Source:
- Import command:
- Idempotency behavior:
- Provenance fields:
- Tests:
- Risks:
