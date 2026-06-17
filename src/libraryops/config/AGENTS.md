# Config Subsystem Rules

## Purpose

This directory owns Django settings modules, root URL wiring, and environment
contract behavior for local, test, and production runs.

## Scope

- `settings/base.py`
- `settings/local.py`
- `settings/test.py`
- `settings/production.py`
- `urls.py`
- `asgi.py`
- `wsgi.py`
- thin include hubs for app-owned URL configs

## Core rules

- `DATABASE_URL` support must remain explicit and tested.
- SQLite fallback behavior must remain explicit for local/test cases.
- Production settings must fail loudly when required environment variables are
  missing.
- Root URL and health-check wiring must remain smoke-testable.
- Environment behavior must not silently drift between local and CI.

## Design rules

- Keep settings layered and explicit.
- Prefer small helper functions for env parsing over repeated inline parsing.
- Do not hide production requirements behind permissive defaults.
- Keep startup/URL behavior compact enough that smoke tests can prove it
  directly.
- Prefer include-based root URL routing over direct view wiring.

## Testing rules

- Settings behavior must remain covered by smoke tests under `tests/smoke/`.
- Any URL or settings contract change must update smoke coverage first.

## Escalation

- Escalate before changing the test DB contract, production env requirements,
  or root URL topology in a way that changes evaluator setup or CI behavior.
