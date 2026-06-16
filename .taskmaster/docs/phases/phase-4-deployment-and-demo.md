# Library Ops Phase 4 PRD View

Canonical source: `.taskmaster/docs/prd.md`

## Goal

Ship a live, evaluator-ready deployment and supporting demo evidence.

## Includes

- Capability `C10 Deployment and Demo Evidence`
- deployment/runbook/README/release slices from `C11 Documentation, Evidence,
  and Reusable Process`

## Exit criteria

- live URL works
- demo accounts work
- README maps requirements to evidence
- release tag corresponds to the deployed commit

## Suggested local regeneration command

```bash
npx --yes --package task-master-ai@0.43.1 -c 'task-master parse-prd .taskmaster/docs/phases/phase-4-deployment-and-demo.md --force'
```
