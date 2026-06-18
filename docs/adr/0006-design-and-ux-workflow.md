# ADR-0006: Design and UX workflow

- Status: accepted
- Date: 2026-06-13
- Deciders: Andrew Crozier

## Context

The demo needs credible UI/UX evidence while remaining implementable without
private design-tool access. The current external design-tool seat available to
this repo is view-only, so it is not a reliable writable implementation lane.

## Decision

`docs/design/wireframes.md` is the repo-local design source of truth. Private
design tools do not form part of the committed control-plane baseline, and
implementation decisions must be represented in repo-local docs and tests.

## Alternatives considered

| Alternative | Benefit | Rejected or adapted because |
|---|---|---|
| External design tool only | Rich visuals | Private or non-writable to many agents and reviewers. |
| Markdown only | Always accessible | Chosen because repo-local authority matters more than a secondary visual system in this branch. |
| No wireframes | Fastest | Increases UI rework and weakens evaluator confidence. |

## Consequences

- Codex can implement UI flows without external design-tool access.
- Accessibility and empty/error states are documented before implementation.

## Validation

- UX tasks must cite wireframes and update them when UI behavior changes.
- E2E/accessibility tests verify key flows after bootstrap.
