# Codex CLI versus IDE extension

The package targets Codex CLI first. The VS Code/Cursor/Windsurf extension is supported as a surface for the same agent, but local handoff instructions must not depend on editor-only context.

| Concern | Codex CLI | Codex IDE extension | Package rule |
|---|---|---|---|
| Configuration | Reads Codex configuration layers and repo `.codex/config.toml`. | Uses the same agent and same configuration, with IDE-specific UI. | Keep `.codex/config.toml` canonical. |
| Context | Receives prompt, repo files, tool output, and explicit attachments. | Can include open files, selections, and editor references. | CLI prompts must name files explicitly. |
| Plan/questions | Use `/plan`; native `request_user_input` is expected where the active build exposes it. | Same planning concept, with richer UI affordances. | Prefer `/plan` before ambiguous implementation. |
| Questionnaires | `ask_user_question` may exist in current interactive builds; verify with the installed feature/tool surface. | UI may make structured questionnaires easier to complete. | Use native questionnaire if available; otherwise output Question packet. |
| Goals | Use `/goal` when enabled. | `/goal` works from the IDE extension too where Goals are available. | Enable `features.goals = true` and write measurable goals. |
| MCP elicitation | `tool_call_mcp_elicitation` surfaces MCP-originated user-input requests in interactive sessions. | Same MCP protocol capability, subject to host support. | Enable `features.tool_call_mcp_elicitation = true`; avoid it in non-interactive `exec`. |
| Cloud work | CLI can run local work and can be paired with cloud workflows where configured. | Extension exposes cloud delegation more directly. | Cloud delegation is derived work; verify locally before merge. |
| Approvals | Terminal approval prompts and configured policy. | Approval modes exposed in UI. | Keep repo policy conservative. |
| Handoff | Copy package, run commands, inspect files. | Can use editor context, but must update repo files. | No critical instruction may live only in editor state. |

## Non-interactive difference

`codex exec` and other non-interactive surfaces should not wait for user-input tooling. If a question is needed, emit the Question packet, set status `needs-user`, and exit non-zero where the command framework allows it.
