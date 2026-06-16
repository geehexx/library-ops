# Clarification, goals, and escalation reference

Use this file as the agent-facing source for clarification, native question
paths, goal quality, and escalation behavior.

## Native question path

Prefer native Codex user-input tooling when the active surface exposes it:

1. `request_user_input` in interactive Plan mode.
2. `ask_user_question` when the active build exposes it.
3. `tool_call_mcp_elicitation` for MCP-originated user input.
4. Plain Question packet only when native paths are unavailable.

Verify the current surface with:

```bash
codex features list
codex --version
```

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

## Goal rule

Use `/goal` only after the outcome is measurable, the evidence surface is
clear, and the stop/ask conditions are explicit. For long-horizon work, omit a
token budget by default unless a hard ceiling is intentional.

## Remote policy blockers

If GitHub or another remote system blocks a required merge, push, or release
step through repository policy, treat that as a real blocker. Do not continue
from an alternate base branch, assume a later merge, or bypass the policy
unless the user explicitly instructs that change. Emit a blocked escalation with
the exact remote evidence first.
