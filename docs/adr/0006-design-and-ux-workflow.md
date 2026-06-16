# ADR-0006: Design and UX workflow

- Status: accepted
- Date: 2026-06-13
- Deciders: user, project coordinator
- Supersedes: ADR-0009

## Context

The demo needs credible UI/UX evidence while remaining implementable without private design-tool access. Figma can improve visual exploration, but Markdown wireframes and accessibility notes must remain available to Codex and reviewers.

## Decision

`docs/design/wireframes.md` is the repo-local design source of truth. Figma MCP is required in the selected toolchain when design extraction is needed and credentials are configured, but private Figma files, tokens, and non-repo state do not become product source of truth. Any Figma-derived decision that affects implementation must be mirrored into repo docs.

## Alternatives considered

| Alternative | Benefit | Rejected or adapted because |
|---|---|---|
| Figma only | Rich visuals | Private/unavailable to many agents and reviewers. |
| Markdown only | Always accessible | Less useful for polished design exploration. |
| No wireframes | Fastest | Increases UI rework and weakens evaluator confidence. |

## Consequences

- Codex can implement UI flows without Figma access.
- Figma remains useful for visual polish and design tokens.
- Accessibility and empty/error states are documented before implementation.

## Validation

- UX tasks must cite wireframes and update them when UI behavior changes.
- E2E/accessibility tests verify key flows after bootstrap.
