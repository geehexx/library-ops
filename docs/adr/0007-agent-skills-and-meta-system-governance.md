# ADR-0007: Agent skills and meta-system governance

- Status: accepted
- Date: 2026-06-13
- Deciders: Andrew Crozier

## Context

Skills, agent instructions, MCP prompts, hooks, and rules are executable process context. They can improve performance, but they can also introduce drift, prompt-injection risk, stale commands, or large always-loaded context.

## Decision

Treat the meta-system as first-class implementation surface:

- Skills must have short unique names, discriminative descriptions, and no redundant project prefix. Reference files are optional and must be concrete when present.
- Agents must know which tools they should use and which tools they should not bypass.
- Do not optimize for thinness as a goal. Important recurring workflows should carry enough top-level context, machine-readable metadata, and linked references that future runs do not have to rediscover them.
- Use `agents/openai.yaml` metadata when it improves skill discovery, UI presentation, default prompting, or dependency declaration.
- Skill and agent changes require validation by `agent-skills-lint` plus focused review of the affected AGENTS/config/docs surfaces. Missing tooling is an implementation-environment defect, not an accepted project mode.
- Third-party skills/prompts are source-reviewed before adoption; copied prose is minimized and references are preserved.
- Meta-system changes that alter permissions, broad tool access, hosted services, paid services, credentials, or context budgets pause for user decision.

## Alternatives considered

| Alternative | Benefit | Rejected or adapted because |
|---|---|---|
| Large AGENTS.md | Simple discovery | Bloats every session and encourages stale instructions. |
| Many tiny skills | Fine-grained | Risk of collisions and poor triggering. |
| One mega-skill | Single discovery point | Too much irrelevant context when invoked. |
| Marketplace skills without review | Fast | Supply-chain and hallucinated-command risk. |

## Consequences

- The skills catalog is smaller, indexed, and linted.
- Meta changes are reviewed like code changes.
- The project can demonstrate agent-governance discipline, not just app code.

## Validation

- `npm run skills:lint` runs the external linter when the package is installed.
- Skill structure and trigger quality are enforced through review and the remaining direct-tool gates rather than a second custom validator.
- `.codex/references/context-and-tooling-strategy.md` remains the compact agent-facing operating summary, with `AGENTS.md`, agent TOMLs, and skills carrying the executable detail while `docs/` stays human-facing.
