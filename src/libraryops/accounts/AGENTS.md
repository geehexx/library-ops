# Accounts Subsystem Rules

## Purpose

This directory owns application roles, permission mapping, auth-adjacent seed
commands, and any future account/profile logic for Library Ops. Demo-user and
role seeding stay here; catalog/import provenance workflows belong with their
owning apps instead of a standalone `seed` app.

## Scope

- `roles.py`
- `permissions.py`
- `management/commands/seed_roles.py`
- `management/commands/seed_demo_users.py`
- any future auth helpers, profile models, or account-scoped tests moved close
  to this module

## Invariants

- Application roles remain the durable source of truth for role names.
- Permission bundles must stay explicit and reviewable.
- Group seeding must be idempotent.
- Demo-user seeding must be idempotent.
- Demo users must not depend on execution order outside explicit role seeding.
- Anonymous access and authenticated-permission failure must stay behaviorally
  distinct.
- Permission checks must stay server-side.
- Object-permission integration must be explicit about which models receive
  which permissions.

## Design rules

- Keep role-name constants and permission-bundle definitions close together.
- Prefer explicit role-definition structures over scattered free-form helpers.
- Keep permission-adjacent logic elegant and compact; avoid a growing pile of
  ad hoc role-check functions.
- If object-level permission rules expand materially, split the policy into a
  dedicated local module rather than bloating `permissions.py`.
- Keep seed command behavior close to Django’s built-in auth/group model rather
  than layering unnecessary abstractions.

## Testing rules

- Accounts mutations must be covered by tests under `tests/`.
- Seed command tests should prove idempotency, role assignment, and permission
  bundle intent.
- If permission behavior changes, add both allow and deny coverage.
- Do not let tests rely on global auth state or accidental ordering.

## Typing rules

- Prefer concrete Django auth model types where the repo is still using the
  default user model.
- Use narrow casts only at dynamic ORM edges.
- Do not reintroduce product-side `TYPE_CHECKING` shim layers for narrow auth
  surfaces without a strong reason.

## Escalation

- Escalate when role design, permission scope, or user-model assumptions would
  change product semantics.
- Escalate before introducing external auth providers that change the local
  demo contract.
