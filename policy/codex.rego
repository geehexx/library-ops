package library_ops.codex

deny contains msg if {
  not input.model_context_window
  msg := "Codex config must declare model_context_window."
}

deny contains msg if {
  input.model_context_window < 500000
  msg := "Main Codex context window must remain at least 500,000 tokens."
}

deny contains msg if {
  input.approval_policy != "on-request"
  msg := "approval_policy must remain on-request."
}

deny contains msg if {
  input.default_permissions != "coordinator_root"
  msg := "default_permissions must remain coordinator_root."
}

deny contains msg if {
  required_features := {"hooks", "enable_request_compression", "multi_agent", "goals", "tool_call_mcp_elicitation"}
  some feature in required_features
  input.features[feature] != true
  msg := sprintf("Codex feature must remain enabled: %s", [feature])
}

deny contains msg if {
  input.agents.max_depth != 2
  msg := "agents.max_depth must remain 2 for the bounded depth-2 specialist posture."
}

deny contains msg if {
  input.agents.max_threads != 24
  msg := "agents.max_threads must remain 24 for the current higher-parallelism posture."
}

deny contains msg if {
  required := {"context7", "exa", "taskmaster-ai", "code-review-graph", "serena"}
  some name in required
  input.mcp_servers[name].required != true
  msg := sprintf("MCP server must be required: %s", [name])
}

deny contains msg if {
  required := {"context7", "exa", "taskmaster-ai", "code-review-graph", "serena"}
  configured := {name | input.mcp_servers[name]}
  missing := required - configured
  count(missing) > 0
  msg := sprintf("Missing required MCP server(s): %v", [missing])
}

deny contains msg if {
  required := {"context7", "exa", "taskmaster-ai", "code-review-graph", "serena"}
  some name in required
  server := input.mcp_servers[name]
  server.default_tools_approval_mode != "approve"
  msg := sprintf("MCP server must default to approve: %s", [name])
}
