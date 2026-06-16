# Context And Artifact Lineage

This file defines the retained context, superseded context, and artifact classes
that shape the repo’s source-of-truth model.

## Artifact classes

### Canonical

The constitution, PRD, supporting specs, `AGENTS.md`, Codex config, skills,
durable docs, CI/policy config, and code/tests define intended behavior.

### Derived

Task Master graph files, Promptfoo outputs, validation logs, SBOMs, graph
indexes, and local export archives prove what happened in a given run. They are
evidence, not product truth.

### Operator-local

Secrets, provider config, OAuth/session state, caches, local databases, and
tool runtime state stay out of version control and out of local exports or
shared evidence bundles.

## Retained context

- Library Ops should be evaluator-ready, not merely scaffolded.
- Borrow/Return terminology resolves the assignment ambiguity better than
  inverted check-in/check-out wording.
- Work, edition, copy, and loan remain distinct domain concepts.
- Roles and quality evidence matter as much as feature count.
- Promptfoo, Task Master, Spec Kit, Serena, code-review-graph, Context7, Exa,
  and Figma each have narrow, evidence-backed roles.

## Superseded context

- Next.js/Supabase/TypeScript as the active stack.
- broad tool exposure without justification.
- Task Master as canonical product truth.
- preserving historical session prose inside durable docs.

## Practical rule

When artifacts disagree:

1. prefer the higher source-of-truth layer
2. regenerate or reconcile the lower derived layer
3. do not reintroduce superseded process or stack choices without a new
   explicit decision
