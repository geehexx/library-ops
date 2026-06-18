---
name: clarify-and-goal
description: Use when a task is ambiguous, needs Codex Plan mode, native user-question tooling, /goal setup, MCP elicitation handling, or when a subagent reports blocked, partial, low-confidence, or needs-user status.
---

# Clarify and Goal

## Purpose

Use this skill to turn ambiguous work into native Codex questions, clear
decision packets, and safe partial work.

Use the installed `$define-goal` skill alongside this one when the main need is
to shape or improve the actual goal text. This repo-local skill owns the
Library Ops routing rules, native question path, and escalation contract.

## Current sources

Treat these as the durable repo-local sources for this workflow:

- `AGENTS.md` for coordinator posture and source order.
- `.taskmaster/docs/prd.md` and `specs/001-core/` for requirements.
- `.codex/agents/*.toml` for agent routing metadata.
- `.agents/skills/code-intelligence/SKILL.md` for tool-routing boundaries.
- `docs/process/quality-gates.md` for the validation ladder.

## Procedure

1. Read the current Task Master task, PRD section, and relevant spec.
2. Decide whether the issue is deterministic or decision-dependent.
3. If deterministic, run the next validation or inspection step.
4. If decision-dependent and interactive Codex exposes native user-input tooling, use it with the Question packet shape.
5. If native user-input tooling is unavailable or non-interactive, print the Question packet and stop with `needs-user`.
6. If the task is long-running, route goal shaping through `$define-goal` and
   keep this skill focused on question/escalation routing.
7. If a subagent raised a concern, normalize it into an Escalation packet, stop
   the blocked branch, and pass it to the coordinator without continuing
   adjacent implementation work.

## Native Codex question preference

Start ambiguous work in `/plan` before choosing implementation steps.

Use the active Codex surface in this order:

1. `request_user_input` in interactive Plan mode when available.
2. `ask_user_question` when the active build exposes the questionnaire UI/tool.
3. MCP elicitation when `tool_call_mcp_elicitation` surfaces a server-originated request.
4. Plain Question packet in the transcript for non-interactive or unsupported surfaces.

Do not add removed or under-development feature flags merely to force a tool. Verify the active surface with `codex features list`.

## Question packet

```text
Question packet
Decision needed:
Why this blocks or changes risk:
Options:
  A. <option> — tradeoff
  B. <option> — tradeoff
Recommended default:
Confidence:
Can proceed without answer? yes/no
Safe partial work while waiting:
Files/tasks affected:
Validation after answer:
```

## Escalation packet

```text
Escalation packet
Status: clear | needs-user | blocked | partial
Confidence: 0.00-1.00
Finding:
Evidence:
Risk if ignored:
User question needed:
Recommended default:
Partial work safe to continue:
Owner agent:
Next validation:
```

Goal text, quantitative outcome shaping, and budget policy live in
`$define-goal`. This skill should only hand goal work off there rather than
owning a second goal template.
