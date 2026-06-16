# SDLC

## Branching

- `main`: release branch.
- `development`: integration branch.
- `feature/TM-<id>-<slug>`: implementation branches.
- `release/vX.Y.Z`: optional release-preparation branch only when a dedicated stabilization branch is justified.

## Pull requests

Every PR must include:

- Task Master task ID.
- PRD/ADR links.
- Test evidence.
- Quality gate results.
- Self-review checklist.

Every control-plane PR should also prove:

- source-of-truth reconciliation across constitution, PRD, Task Master, AGENTS,
  skills, ADRs, and docs when any of those surfaces move;
- whether claimed local-model or MCP behavior was actually exercised;
- which review threads were closed by the current head.

Dependency automation should follow the same integration path:

- Dependabot PRs target `development`, not `main`.
- Dependency PRs still require the normal quality, policy, and workflow gates.
- Release movement still happens only through the `development` -> `main` path.

## Release

- Conventional Commits drive SemVer.
- `development` merges into `main` via release PR.
- Python Semantic Release owns version and changelog generation.
- The current GitHub workflow is a readiness check, not a publishing workflow:
  it must prove changelog and version generation can run without committing,
  tagging, pushing, or creating a remote release.

## Enforcement

The SDLC is not only descriptive. CI job names, policy checks, docstring gates,
ADR index validation, Task Master dependency validation, and the documented PR
evidence path are all part of the enforceable contract and should stay aligned
with this document. If a remote repository policy blocks a required step, treat
that as an explicit blocker instead of working around it.
