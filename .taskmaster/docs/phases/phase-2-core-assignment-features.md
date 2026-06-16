# Library Ops Phase 2 PRD View

Canonical source: `.taskmaster/docs/prd.md`

## Goal

Finish the required assignment product flows: catalog management, circulation,
 and baseline search.

## Includes

- Capability `C4 Catalog Management`
- Capability `C5 Circulation`
- Capability `C6 Search and Discovery`

## Exit criteria

- evaluator can complete required flows locally
- role boundaries are enforced
- search returns exact identifiers ahead of broader matches
- property tests cover circulation invariants

## Suggested local regeneration command

```bash
npx --yes --package task-master-ai@0.43.1 -c 'task-master parse-prd .taskmaster/docs/phases/phase-2-core-assignment-features.md --force'
```
