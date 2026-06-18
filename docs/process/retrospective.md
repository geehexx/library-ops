# Retrospective Process

## When to run

- End of significant Codex session.
- After failed checks.
- After repeated user correction.
- Before changing AGENTS.md, skills, PRD, or CI.

## Questions

1. What was completed?
2. What failed or stalled?
3. What assumptions were unsupported?
4. Was the missing instruction global, local, task-specific, or tooling-related?
5. Can the issue be prevented by an automated check?
6. Should the update go to AGENTS.md, nested override, skill, PRD/ADR, Task Master, CI/tooling, or nowhere?
7. Should the lesson also be written into memory so future runs do not have to rediscover it?
8. Should the lesson update `.codex-session-notes/continuation.md` or the
   startup/handoff workflow?

## Rule

Do not expand root AGENTS.md unless the instruction is global and recurring.

Promote repeated lessons in this order:

1. deterministic config, rule, or test enforcement
2. AGENTS / nested AGENTS / agent TOML
3. skill workflow or skill reference
4. PRD / ADR / Task Master note
5. memory only when the lesson is durable but not yet ready for tracked promotion
