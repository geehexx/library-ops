# Prompting and context patterns

## Durable instruction hierarchy

1. Root `AGENTS.md`.
2. Nested `AGENTS.md` files.
3. `.codex/agents/*.toml` specialist instructions.
4. `.agents/skills/*/SKILL.md` progressive-disclosure workflows.
5. Current Task Master task and PRD/spec sections.

## Context ladder

1. Direct source/test inspection.
2. Serena for symbol retrieval.
3. code-review-graph for blast-radius context.
4. ast-grep for structural queries.
5. Context7 for library docs.
6. Exa for current external research.
7. Repomix only for bounded snapshots.
8. RTK for noisy output; raw logs for evidence.

## Research Evidence Ladder

1. Canonical repo docs, current Task Master task, PRD/spec, and local command
   evidence.
2. Official docs, standards, release notes, and primary upstream repositories.
3. Context7 for version-specific library/API documentation.
4. Exa and web search for current discovery, counter-evidence, and source
   expansion.
5. Community sources such as Reddit only as low-confidence hypothesis signals.
6. Spark summarization only after URLs, dates, and claims are separated from
   primary evidence.

Do not promote anecdotal claims into ADRs, Task Master notes, or accepted
agent-system policy unless they are confirmed by primary sources or local
validation evidence.

## Clarification ladder

1. Resolve from canonical docs.
2. Ask subagents for Escalation packets.
3. Use `/plan` for ambiguous work.
4. Use native `request_user_input`, `ask_user_question`, or MCP `tool_call_mcp_elicitation` when the active Codex surface exposes them.
5. If native user-input is unavailable, ask with a Question packet and stop.
6. Set `/goal` only after success criteria are measurable.
