---
name: retrospective
description: Use when a session ends, checks fail, user corrections arrive, or AGENTS/skills/process instructions may need improvement.
---

# Retrospective Skill

## Goal

Improve the agent system without bloating always-on context.
When a recurring workflow branches, prefer recording a bounded child-worker
handoff and the Spark lane cue rather than flattening the lesson into a wider
local pass.

## Process

1. Summarize outcome.
2. Identify friction and root causes.
3. Classify update target: AGENTS.md, nested override, skill, PRD/ADR, Task Master, CI/tooling, or no action.
4. Prefer skill updates over root AGENTS.md updates.
5. Prefer automated checks over prose.
6. Return proposed patches separately.

## Durable lessons

- If the friction is repeated root-level replanning, over-broad ownership, or
  a missing Spark lane cue, prefer the narrowest routing surface first:
  coordinator TOML for delegation, implementer TOML for slice boundaries, or
  code-intelligence for tool-ladder changes.
- If the lesson is truly recurring and global, promote it out of this skill;
  otherwise keep it here or in `docs/process/retrospective.md`.
- If the same lesson is likely to recur, prefer a tracked skill, agent TOML,
  or docs update before writing anything to memory.
- If a branch is rewritten, force-pushed, or replaced, refresh live PR checks
  and mergeability evidence against the current head before treating older
  results as truth.

## Output

- Outcome:
- Friction:
- Root cause:
- Proposed improvement:
- Recommended file:
- Proposed patch:
- Do not change:
