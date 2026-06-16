# PRD Format Comparison

## Decision

Use **RPG PRD** as the canonical Task Master PRD, enhanced with:

- ISO/IEEE-style requirements precision,
- ADR decision records,
- C4/arc42-inspired architecture sections,
- BDD/Gherkin acceptance criteria,
- security/accessibility quality gates,
- Task Master dependency parsing.

When constrained local models cannot reliably process the full canonical PRD,
derive bounded phase PRDs from the canonical document instead of inventing a
second planning format.

## Alternatives

| Format | Strength | Weakness | Decision |
|---|---|---|---|
| Flat Product PRD | Low-friction for human review | Weak dependency graph | Not canonical |
| ISO/SRS | Precise requirements | Too heavy alone | Use within RPG sections |
| Amazon PRFAQ | Customer clarity | Not task-generation optimized | Use for executive summary only if needed |
| RPG PRD | Dependency-aware, taskable | Needs discipline | Canonical |
| arc42/iSAQB | Architecture views | Too much as standalone | Adapt selected views |
| BDD-only | Testable behavior | Incomplete product/architecture context | Use in acceptance criteria |

## Practical output rule

The canonical PRD must stay rich enough for human review and repo governance.
Phase PRDs, Spec Kit feature plans, and Task Master tasks exist to make that
canonical contract executable, not to compete with it.
