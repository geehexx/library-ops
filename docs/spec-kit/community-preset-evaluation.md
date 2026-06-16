# Spec Kit Community Preset Evaluation

## Policy

Community presets are useful, but not trusted by default. Source must be reviewed before installation. When a preset concept is valuable but the code is unnecessary, adapt the concept into PRD/AGENTS/skills instead of installing the preset.

## Selected preset strategy

| Preset | Decision | Reason |
|---|---|---|
| A11Y Governance | Adapt concept; do not install by default | Accessibility checks and WCAG 2.2 AA matter, but the preset source must be reviewed before adopting executable templates. |
| Agent Parity Governance | Adapt concept; do not install by default | Agent parity is useful, but repo-local Codex/Task Master rules already encode the selected workflow. |
| Architecture Governance | Adapt concept; do not install by default | Architecture governance concepts are already captured in the consolidated ADRs and quality gates. |
| Explicit Task Dependencies | Adapt concept; do not install by default | Task dependency discipline is already embedded in the Spec Kit tasks and Task Master guidance. |
| Security Governance | Adapt concept; do not install by default | Security SDLC concepts are already captured in CI, policy, PR template, and ADR-0005. |
| Table of Contents Navigation | Adapt concept; do not install by default | Navigation is handled through README, ADR index, PRD structure, and docs directories. |
| Workflow Preset | Study only; do not install by default | Behavior-first handoffs may overlap with our required Task Master/Spec Kit/Codex agent workflow. |
| iSAQB Architecture Governance | Adapt selected arc42/C4 ideas; do not install by default | Valuable architecture views, but executable preset adoption would be heavier than needed now. |
| Cross-Platform Governance | Adapt script parity ideas; do not install by default | Useful for bootstrap scripts, but not part of the required selected implementation stack. |
| AIDE In-Place Migration | Reject | Migration-specific; not this project. |
| Canon Core | Reject for now | Requires/targets Canon workflow; not needed. |
| Claude AskUserQuestion | Reject for Codex primary workflow | Claude-specific UX enhancement. |
| VS Code Ask Questions | Reject for current workflow | Not core to Codex CLI workflow. |
| Jira Issue Tracking | Reject | We use GitHub/Task Master, not Jira. |
| Model Driven Engineering | Reject for now | Requires MDE extension and adds scope. |
| Multi-Repo Branching | Reject | Single repo project. |
| Spec2Cloud | Reject | Azure-specific; Render/Postgres deployment planned. |
| Pirate Speak | Reject | Demonstration anti-pattern. |
| Fiction Book Writing | Reject | Domain-inappropriate. |
| Game Narrative Writing | Reject | Domain-inappropriate. |
| Screenwriting | Reject | Domain-inappropriate. |
| Canon/AIDE derivative presets | Reject unless scope changes | Avoid workflow drift. |

## Source-review commands

Use these to inspect candidates. Do not install presets until a future task records a source-review decision:

```bash
uvx --from git+https://github.com/github/spec-kit.git@v0.10.2 specify --version
specify preset info spec-kit-preset-agent-parity-governance
specify preset info spec-kit-preset-architecture-governance
specify preset info spec-kit-preset-security-governance
specify preset info spec-kit-preset-explicit-task-dependencies
specify preset info spec-kit-preset-toc-navigation

# After a future source-review decision, installation would use:
# specify preset add <preset-id> --priority <priority>

specify preset list
specify preset resolve spec-template
specify preset resolve plan-template
specify preset resolve tasks-template
```

## Source-review procedure

Before adopting any preset:

1. review `preset.yml`, commands, templates, and scripts
2. confirm no command requests secrets or destructive operations
3. confirm it does not replace the canonical source-of-truth order
4. record the decision in an ADR only if it changes architecture, security,
   external dependencies, or agent authority

## Rollback

```bash
specify preset disable <preset_id>
specify preset remove <preset_id>
specify preset list
```

## Rationale

The adopted governance concepts are already codified in:

- `.specify/memory/constitution.md`
- `.taskmaster/docs/prd.md`
- `.codex/agents/*.toml`
- `.agents/skills/*/SKILL.md`
- `docs/adr/*.md`
- GitHub workflows and PR templates
