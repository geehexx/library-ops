# Library Ops Phase 4 PRD View

Canonical source: `.taskmaster/docs/prd.md`

## Goal

Ship a live, evaluator-ready deployment and supporting demo evidence.

## Includes

- Capability `C10 Deployment and Demo Evidence`
- deployment/runbook/README/release slices from `C11 Documentation, Evidence,
  and Reusable Process`

## Entry criteria

- Phase 3 or an intentionally trimmed equivalent is merged
- demo accounts, seed flows, and assignment-critical checks are stable locally
- release-readiness commands are trustworthy on `development`

## Implementation notes

- Treat README, runbook, changelog, demo script, and release surfaces as one
  coherent evaluator package instead of scattering separate evidence docs.
- Deployment evidence must prove migrations, static assets, seed flows, and the
  documented demo accounts against the real target environment.
- The first actual release remains `0.1.0` and should only be cut after the
  evaluator-basic slice is proven on `development`.

## Out of scope

- speculative platform-specific polish that does not improve evaluator
  confidence
- creating release tags before the real release branch/PR is ready

## Exit criteria

- live URL works
- demo accounts work
- README maps requirements to evidence
- release tag corresponds to the deployed commit

## Suggested local regeneration command

```bash
npx --yes --package task-master-ai@0.43.1 -c 'task-master parse-prd .taskmaster/docs/phases/phase-4-deployment-and-demo.md --force'
```
