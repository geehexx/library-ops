# Library Ops Phase 1 PRD View

Canonical source: `.taskmaster/docs/prd.md`

## Goal

Build the Django bootstrap, domain model, and RBAC foundation.

## Includes

- Capability `C1 Project Foundation`
- Capability `C2 Library Domain Model`
- Capability `C3 Authentication and RBAC`

## Exit criteria

- `manage.py check` passes
- migrations apply cleanly
- demo users and roles exist
- domain constraints and RBAC checks are tested

## Suggested local regeneration command

```bash
npx --yes --package task-master-ai@0.43.1 -c 'task-master parse-prd .taskmaster/docs/phases/phase-1-bootstrap-domain-rbac.md --force'
```
