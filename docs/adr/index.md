# Architecture decision records

ADRs are reserved for decisions that affect structure, quality attributes, external dependencies, operational posture, or agent/tool permissions. Policy details, research notes, and runbook steps belong in supporting docs.

| ADR | Status | Decision |
|---|---|---|
| [ADR-0001](0001-source-of-truth-and-planning-model.md) | accepted | Source of truth and planning model. |
| [ADR-0002](0002-application-architecture-and-domain-boundaries.md) | accepted | Hybrid C4/arc42/pragmatic-domain architecture and Django boundaries. |
| [ADR-0003](0003-search-ai-and-data-provenance.md) | superseded | Exact-identifier-first lexical search and deterministic seeded data. |
| [ADR-0004](0004-agent-toolchain-mcp-and-context-optimization.md) | accepted | Required Codex/MCP/context/code-intelligence toolchain. |
| [ADR-0005](0005-delivery-quality-security-and-release.md) | accepted | Delivery, quality, security, release, and deployment governance. |
| [ADR-0006](0006-design-and-ux-workflow.md) | accepted | Repo-local wireframes as the design authority. |
| [ADR-0007](0007-agent-skills-and-meta-system-governance.md) | accepted | Agent skills and meta-system governance. |
| [ADR-0008](0008-two-level-agent-orchestration-and-spark-fanout.md) | accepted | Hybrid direct-specialist orchestration with Spark micro-workers. |

## Superseded ADR mapping

The earlier 19-record set was consolidated because many entries were process notes rather than architecturally significant decisions. The superseding ADRs list their absorbed records in their headers.

The repository governance tests also require this index to match the committed
ADR file set so index drift becomes a CI-visible failure instead of a manual
cleanup task.

## ADR format

New ADRs should use:

```text
# ADR-XXXX: Title

- Status: proposed | accepted | superseded | rejected
- Date: YYYY-MM-DD
- Deciders: people/roles
- Supersedes: optional

## Context
## Decision
## Alternatives considered
## Consequences
## Validation
```

Do not create an ADR for every small tool flag, task note, or documentation edit. Use ADRs when the decision is expensive, risky, structural, externally coupled, or likely to be questioned later.
