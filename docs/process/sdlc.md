# SDLC

## Branching

- `main`: release branch, protected.
- `development`: integration branch, protected.
- `feature/TM-<id>-<slug>`: implementation branches.
- `release/vX.Y.Z`: optional release-preparation branch only when a dedicated stabilization branch is justified.

## Pull requests

Every PR must include:

- Task Master task ID.
- PRD/ADR links.
- Test evidence.
- Quality gate results.
- Self-review checklist.

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
