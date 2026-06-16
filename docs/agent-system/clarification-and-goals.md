---
id: DOC-CLARIFICATION-GOALS
title: Clarification, Native User Questions, Goal Setting, and Escalation
status: active
last_reviewed: 2026-06-13
related_adrs:
  - ../adr/0007-agent-skills-and-meta-system-governance.md
---

# Clarification, native user questions, goal setting, and escalation

## Current Codex feature understanding

This package targets the latest Codex CLI behavior reported by the user for the implementation machine:

```text
collaboration_modes                  removed            true
default_mode_request_user_input      under development  false
goals                                stable             true
hooks                                stable             true
multi_agent                          stable             true
tool_call_mcp_elicitation            stable             true
enable_request_compression           stable             true
```

The package therefore enables modern stable features that matter to the control plane:

```toml
[features]
hooks = true
enable_request_compression = true
multi_agent = true
goals = true
tool_call_mcp_elicitation = true
```

Do **not** add `collaboration_modes = true` to project config. Older issues mention that flag for Plan mode, but the latest feature list says it is removed and already true in the target build. Do **not** depend on `default_mode_request_user_input` because the user-provided feature list marks it under development and false.

## Native question mechanism

Prefer native Codex user-question tooling when the active surface exposes it:

1. In interactive Codex CLI/IDE Plan mode, use the native `request_user_input` path when available.
2. If the build exposes `ask_user_question`, use it for small, constrained-choice questionnaires.
3. If the question is triggered by an MCP server, let `tool_call_mcp_elicitation` surface the MCP elicitation through Codex.
4. If running non-interactively, or the native question tool is unavailable, output a Question packet and stop with `needs-user`.

The repository does not pretend that a single tool name works in every Codex surface. The active implementation environment must verify with:

```bash
codex features list
codex --version
```

Relevant evidence:

- public Codex issue evidence shows `request_user_input` existed in Plan mode and was previously unavailable in code mode;
- public Codex issues and workflow names show `ask_user_question` exists or has existed as an interactive questionnaire path in some builds;
- latest user-provided feature output shows `tool_call_mcp_elicitation` stable and enabled;
- Codex Goal documentation treats Goals as persistent, evidence-checked objectives with lifecycle commands.

## When Codex should ask

Ask before implementation when any of these are true:

- more than one valid product or architecture path exists;
- a required credential, paid service, hosted code export, or new MCP is involved;
- a subagent reports confidence below 0.75 on a blocking recommendation;
- implementation would create irreversible migration, git, deployment, or branch-protection state;
- a task is partially implementable but the unimplemented portion depends on user preference;
- source-of-truth files contradict each other;
- a goal cannot be expressed with measurable completion criteria;
- the agent would otherwise guess at user intent, business priority, privacy posture, or cost tolerance.

Do not ask when the next step is a deterministic validation command, a required local setup smoke test, or direct inspection of canonical files.

## Question packet shape

Use the native question tool with this shape when possible; otherwise print the packet and stop:

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

Questions must be answerable. Prefer two to five options and include the recommended default unless the evidence is genuinely balanced. Never ask a vague “what should I do?” question when a smaller decision packet would work.

## Subagent escalation packet

Every specialist subagent should return this packet when it finds ambiguity, risk, low confidence, or partial work:

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

Subagents do not directly interrupt the user. They bubble the packet to the
coordinator. The coordinator then decides whether to continue safe partial work,
call a native user-input tool, produce a Question packet, route Task Master
mutation through `taskmaster_governor`, or stop.

## Goal setting workflow

Use `/goal` for long or multi-turn Codex work after planning. A valid goal must include:

- outcome;
- verification surface;
- files or artifact classes in scope;
- constraints;
- iteration policy;
- validation commands;
- definition of done;
- stop/ask conditions.

Token budgets are optional lifecycle controls, not part of the completion contract. For long-horizon work, omit `token_budget` by default and rely on measurable completion criteria plus blocked-stop conditions. Set a token budget only when there is a concrete reason for a hard stop, cost ceiling, or deliberate summarize-and-handoff checkpoint.

If a goal becomes `budget_limited`, treat it as non-complete. The correct response is a progress handoff with evidence collected, blockers, and the next best validation step, not a success claim.

Strong goal template:

```text
/goal <outcome>, verified by <evidence>, while preserving <constraints>. Use only <allowed files/tools/context>. Between iterations, record what changed, what evidence showed, and the next best step. If blocked, low-confidence, or user input is needed, stop with a Question packet and Escalation packet summary.
```

If the goal is hard to define, start with `/plan` and ask Codex to interview the user before setting `/goal`.

## CLI versus IDE notes

- Codex CLI is the primary handoff target for this repo.
- The IDE extension uses the same agent and shared configuration, but it can add IDE context such as open files, selections, and cloud delegation surfaces.
- CLI handoff instructions must be self-contained because the CLI does not automatically know which IDE tabs are open.
- VS Code extension work must still commit the same canonical files and run the same gates.
- Do not rely on IDE-only state to satisfy a Task Master note, PR checklist, or release evidence requirement.

## Non-interactive safety

Do not rely on interactive question popups in `codex exec` or other non-interactive runs. Known public issue evidence shows MCP/user-input paths can be unsupported or cancelled in exec mode. In non-interactive mode, fail fast with a Question packet in the output and mark the task `needs-user` rather than waiting for input.
