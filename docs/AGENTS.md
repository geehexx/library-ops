# Documentation agent rules

- Keep documentation in Diátaxis categories.
- Keep repo-wide agent-operating instructions in `../AGENTS.md`, `.codex/`,
  `.taskmaster/`, or skill references; keep docs-local workflow rules here only
  when they support documentation maintenance.
- Use `../SETUP.md` for bootstrap and recurring operator commands.
- Use `ARCHITECTURE.md` for architecture rationale and validation.
- Keep ADRs for architecturally significant decisions only and maintain
  `docs/adr/index.md` when ADR files change.
- Run documentation quality gates after doc changes.
- Treat Spec Kit community preset ideas as study-only; adapt useful concepts
  into `PRD`/`AGENTS`/skills/ADRs instead of installing standalone preset docs
  by default.

## Decisioning and escalation

Use explicit alternatives, counterfactual evidence, and validation for material
tool/process choices. The decision-status taxonomy is:

- Required selected stack
- Accepted
- Recommended default
- Task-scoped required
- Benchmark candidate
- Deferred
- Rejected for now

Pause and ask for a user decision before:

- adding paid or hosted services;
- exporting source code to a cloud indexing/search platform;
- introducing credentials, OAuth, new secret handling, or new vendors;
- changing the product scope, UI stack, deployment target, or demo requirements;
- increasing subagent depth, allowing recursive fan-out, or materially
  changing context budgets;
- pushing irreversible repository state if branch or repo intent is unclear;
- replacing an accepted tool with a materially different trust, cost, or
  security profile.

Do not pause merely because:

- a required local tool needs configuration;
- a smoke test can be run safely;
- docs, skills, or scripts need updating to reflect an accepted decision;
- a constrained sandbox lacks a required binary and the blocker can be reported.

For material decisions, record the required decision block in Task Master notes
or the relevant ADR:

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

Accepted stack decisions and tool policy live in ADRs and repo policy files;
this document only captures the docs-local workflow posture.
