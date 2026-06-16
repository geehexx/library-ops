# PRD Format Comparison

## Decision

Use **RPG PRD** as the canonical Task Master PRD, enhanced with:

- ISO/IEEE-style requirements precision,
- ADR decision records,
- C4/arc42-inspired architecture sections,
- BDD/Gherkin acceptance criteria,
- security/accessibility quality gates,
- Task Master dependency parsing.

## Alternatives

| Format | Strength | Weakness | Decision |
|---|---|---|---|
| Flat Product PRD | Easy to read | Weak dependency graph | Not canonical |
| ISO/SRS | Precise requirements | Too heavy alone | Use within RPG sections |
| Amazon PRFAQ | Customer clarity | Not task-generation optimized | Use for executive summary only if needed |
| RPG PRD | Dependency-aware, taskable | Needs discipline | Canonical |
| arc42/iSAQB | Architecture views | Too much as standalone | Adapt selected views |
| BDD-only | Testable behavior | Incomplete product/architecture context | Use in acceptance criteria |
