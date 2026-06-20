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
9. Was the main friction root-level JIT planning, and if so should the fix be
   a coordinator/implementer routing rule instead of another general AGENTS.md
   change?
10. Would a Spark lane cue, bounded child-worker cue, single-file fixer rule,
    or debugger-pass cue have prevented the repeat work?
11. If the same lesson has appeared more than once, should it move into a
    skill, agent TOML, or tracked doc before it is written to memory?

## Rule

Do not expand root AGENTS.md unless the instruction is global and recurring.
If the lesson is about repetitive delegation friction, over-broad planning, or
debugger ownership, try `.codex/agents/coordinator.toml`,
`.codex/agents/implementer.toml`, or the relevant skill before touching root
AGENTS.

Promote repeated lessons in this order:

1. deterministic config, rule, or test enforcement
2. agent TOML for routing, ownership, or Spark lane cues
3. skill workflow or skill reference
4. AGENTS / nested AGENTS only when the lesson must be global
5. PRD / ADR / Task Master note
6. memory only when the lesson is durable but not yet ready for tracked promotion

If the issue is repeated replanning or ownership drift, prefer the narrowest
tracked routing surface first: coordinator TOML, implementer TOML, or the
relevant skill. Keep root AGENTS lean unless the lesson truly applies
everywhere.

If the lesson is about Spark-first branch handling or bounded child-worker fan-out, promote it into the execution-lane TOMLs before broadening to AGENTS.

If the default is still soft after the first pass, harden the primary sources
first (`AGENTS.md`, coordinator TOML, and the matching skill), then pin the
new wording in the control-plane tests before widening to mirrored surfaces
like the startup banner.

When the live Task Master pointer changes, refresh
`.codex-session-notes/continuation.md` in the same checkpoint so the next
session does not inherit stale task IDs or stale next-task guidance.

If the repository already provides a dedicated Task Master governor agent
(`.codex/agents/taskmaster-governor.toml`), treat that as the first routing
surface for Task Master graph mutations instead of implying the role does not
exist. If a lesson keeps recurring, add it to the tracked backlog or routing
docs before writing it to memory.

If the workspace or other operational default is already known from repo
context or the user, do not spend a turn re-asking for it. Use the default and
keep moving unless the choice changes scope or risk.

Community shorthand "Ralph loop" maps to the repo's bounded continuation loop:
continue, checkpoint, evidence, handoff.
