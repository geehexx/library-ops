# Question, native user-input, and escalation packet schema

Use this schema from `/plan` before high-risk work and from `/goal` stop/ask conditions during long-running work.

## Native Codex question preference

When interactive Codex exposes a native user-question mechanism, use it. The desired shape is a structured questionnaire, not free-form ambiguity:

- `request_user_input` in interactive Plan mode where available.
- `ask_user_question` where the active build exposes it.
- MCP elicitation via `tool_call_mcp_elicitation` for MCP-server-originated questions.

If no native mechanism is available, output the Question packet below and stop.

## Question packet

Required fields:

- `Decision needed`
- `Why this blocks or changes risk`
- `Options`
- `Recommended default`
- `Confidence`
- `Can proceed without answer?`
- `Safe partial work while waiting`
- `Files/tasks affected`
- `Validation after answer`

Required option discipline:

- two to five options;
- one recommended default when possible;
- explicit tradeoff for each option;
- no hidden “surprise default” if the user does not answer;
- no credential, cloud, cost, or irreversible action without user approval.

## Escalation packet

Required fields:

- `Status`
- `Confidence`
- `Finding`
- `Evidence`
- `Risk if ignored`
- `User question needed`
- `Recommended default`
- `Partial work safe to continue`
- `Owner agent`
- `Next validation`

## Status values

- `clear`: no user input required.
- `needs-user`: user answer required before material action.
- `blocked`: cannot proceed safely.
- `partial`: safe partial work exists but a decision remains.

## Confidence values

Use a 0.00-1.00 score:

- `>= 0.90`: high confidence; cite evidence and proceed if no decision gate applies.
- `0.75-0.89`: proceed only for reversible work; note validation needed.
- `< 0.75`: bubble an Escalation packet; coordinator decides whether to ask.
- `< 0.60`: stop unless there is explicitly safe inspection-only work.
