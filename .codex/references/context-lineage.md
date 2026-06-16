# Context and artifact lineage reference

Use this file as the agent-facing summary of artifact classes and disagreement
resolution.

## Artifact classes

- Canonical: constitution, PRD, supporting specs, `AGENTS.md`, Codex config,
  skills, durable docs, CI/policy config, and code/tests.
- Derived: Task Master graph files, Promptfoo outputs, validation logs, SBOMs,
  graph indexes, and export archives.
- Operator-local: secrets, provider config, OAuth/session state, caches, local
  databases, and tool runtime state.

## Practical rule

When artifacts disagree:

1. prefer the higher source-of-truth layer;
2. regenerate or reconcile the lower derived layer;
3. do not reintroduce superseded process or stack choices without a new
   explicit decision.
