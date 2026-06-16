---
id: DOC-SOCRATIC-DECISION-FRAMEWORK
title: Socratic Decision Framework
status: active
last_reviewed: 2026-06-13
---

# Socratic Decision Framework

## Purpose

The project makes consequential choices through explicit questions, alternatives, counterfactual evidence, and validation. The framework prevents unexamined tool adoption while avoiding unnecessary pauses for choices the user has already made.

## Decision statuses

| Status | Meaning |
|---|---|
| Required selected stack | User intent and project docs require the tool/process in real implementation environments. Missing local installation is an environment issue. |
| Accepted | Explicitly approved or already captured in an ADR/PRD. |
| Recommended default | Good default after alternatives review, reversible, and low risk. |
| Task-scoped required | Required when that task type is active, such as Figma MCP for Figma-backed design work. |
| Benchmark candidate | Promising, but needs a benchmark or task-specific proof before adoption. |
| Deferred | Not adopted without a new user decision. |
| Rejected for now | Mismatch with project scope or constraints. |

## Pause rules

Pause and ask the user before:

- adding paid or hosted services;
- exporting source code to a cloud indexing/search platform;
- introducing credentials, OAuth, new secret handling, or new vendors;
- changing the product scope, UI stack, deployment target, or demo requirements;
- increasing subagent depth, allowing recursive fan-out, or materially changing context budgets;
- pushing irreversible repository state if branch/repo intent is unclear;
- replacing an accepted tool with a materially different trust/cost/security profile.

Do not pause merely because:

- a required local tool needs configuration;
- a smoke test can be run safely;
- docs/skills/scripts need updating to reflect an accepted decision;
- a constrained sandbox lacks a required binary and a report can identify the blocker.

## Required decision block

```text
Decision status:
User tie-back:
Problem:
Alternatives considered:
Counterfactual evidence:
Recommendation:
Validation/smoke test:
Security/cost/privacy impact:
Rollback:
Open question:
```

## Simulated review panel method

Use this internally for material decisions and summarize the result, not private reasoning.

| Panel role | Focus |
|---|---|
| Delivery lead | Can this ship predictably through Task Master and CI? |
| Django architect | Is this idiomatic Django rather than framework cosplay? |
| Domain modeler | Are invariants explicit without full DDD overreach? |
| Security engineer | Does this add a trust, secret, MCP, or supply-chain risk? |
| QA engineer | Are there executable gates and failure signals? |
| Tooling skeptic | Is a smaller existing tool better than a broad platform? |
| Context economist | Does this reduce context or just add complexity? |
| Devil’s advocate | What evidence would make this wrong? |

Rotate in UX, search, deployment, or data-provenance reviewers when the decision affects those areas.

## Current accepted decisions

| Area | Decision |
|---|---|
| Main agent | Codex CLI with project-local config, skills, hooks, subagents, and MCPs. |
| Context | Main context window target is 1,000,000 tokens; subagents are bounded. |
| Fan-out | Direct specialists only; recursive fan-out disabled. |
| Tool stack | RTK, code-review-graph, Serena, ast-grep, Repomix, agent-skills-lint, actionlint, zizmor, Conftest, Gitleaks, Semgrep, pip-audit, npm audit are required in implementation environments. |
| Architecture | Hybrid C4 + arc42 quality/risk framing + pragmatic domain boundaries. |
| DDD | Use bounded contexts and invariants, not full enterprise tactical DDD ceremony. |
| PRD/tasks | PRD is canonical for Task Master; Spec Kit supports governance and consistency. |
| Root docs | Root remains navigational; deep rationale lives under `docs/`. |

## Documentation placement

| Content | Location |
|---|---|
| Product WHAT and acceptance criteria | `.taskmaster/docs/prd.md` |
| Task graph | `.taskmaster/tasks/tasks.json` after parse |
| Architecture decisions | `docs/adr/` |
| Alternatives and evidence | `.taskmaster/docs/prd.md`, `docs/adr/`, `docs/reference/context-lineage.md`, Task Master notes |
| Operating procedures | `docs/runbook.md`, `docs/process/` |
| Agent workflow | `AGENTS.md`, `.codex/agents/`, `.agents/skills/` |
| Design source | `docs/design/wireframes.md` |
