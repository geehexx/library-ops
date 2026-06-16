---
id: TASKMASTER-RUNTIME-POLICY
title: Task Master Runtime and Commit Policy
status: active
last_reviewed: 2026-06-16
related_prd: ./prd.md
---

# Task Master Runtime and Commit Policy

## Purpose

Keep Task Master-specific runtime guidance under `.taskmaster/` instead of
spreading machine-specific provider setup, dependency tactics, and commit rules
through the general repo docs.

## Repo contract

Committed:

- `.taskmaster/docs/prd.md`
- `.taskmaster/tasks/tasks.json`
- `.taskmaster/config.example.json`
- `.taskmaster/AGENTS.md`
- this file

Local-only:

- `.taskmaster/config.json`
- `.taskmaster/state.json`
- `.taskmaster/tasks/*.md`
- `.taskmaster/reports/`

Do not commit provider keys, OAuth state, or ad hoc local exports.

## Source-of-truth rule

1. `.taskmaster/docs/prd.md` is the canonical Task Master input.
2. `.taskmaster/tasks/tasks.json` is a reviewed derived execution artifact.
3. Generated tasks must still be reconciled against `specs/001-core/tasks.md`
   and the active ADR set before implementation.

## Recommended local profiles

### Profile A: local-first low-cost

Use this when you want the cheapest repo-local generation path and already have
Ollama running:

```json
{
  "models": {
    "main": {
      "provider": "ollama",
      "modelId": "qwen2.5-coder:3b",
      "maxTokens": 64000,
      "temperature": 0.1,
      "baseURL": "http://127.0.0.1:11434/api"
    },
    "research": {
      "provider": "ollama",
      "modelId": "qwen2.5-coder:3b",
      "maxTokens": 128000,
      "temperature": 0.1,
      "baseURL": "http://127.0.0.1:11434/api"
    },
    "fallback": {
      "provider": "codex-cli",
      "modelId": "gpt-5.4-mini",
      "maxTokens": 64000,
      "temperature": 0.1
    }
  },
  "global": {
    "logLevel": "info",
    "debug": false,
    "defaultSubtasks": 5,
    "defaultPriority": "medium",
    "defaultTag": "master",
    "projectName": "Library Ops",
    "ollamaBaseURL": "http://127.0.0.1:11434/api",
    "anonymousTelemetry": false
  }
}
```

### Profile B: Codex CLI escalation

Use this when local generation quality is not good enough and the operator has
working Codex CLI auth:

```json
{
  "models": {
    "main": {
      "provider": "codex-cli",
      "modelId": "gpt-5.4-mini",
      "maxTokens": 64000,
      "temperature": 0.1
    },
    "research": {
      "provider": "codex-cli",
      "modelId": "gpt-5.4-mini",
      "maxTokens": 64000,
      "temperature": 0.1
    },
    "fallback": {
      "provider": "codex-cli",
      "modelId": "gpt-5.4",
      "maxTokens": 64000,
      "temperature": 0.1
    }
  },
  "global": {
    "logLevel": "info",
    "debug": false,
    "defaultSubtasks": 5,
    "defaultPriority": "medium",
    "defaultTag": "master",
    "projectName": "Library Ops"
  }
}
```

## Setup flow

```bash
cp .taskmaster/config.example.json .taskmaster/config.json
npx --yes --package task-master-ai@0.43.1 -c 'task-master models --setup'
npx --yes --package task-master-ai@0.43.1 -c 'task-master models'
npx --yes --package task-master-ai@0.43.1 -c 'task-master validate-dependencies'
npx --yes --package task-master-ai@0.43.1 -c 'task-master next'
```

Use `models --setup` to repair local config. Do not edit `.taskmaster/state.json`
manually.

## Dependency and audit policy

- Do not run `npm audit fix --force`.
- Keep the Task Master command and MCP surface version-pinned.
- Prefer a pinned external CLI/MCP invocation over re-vendoring `task-master-ai`
  into the repo-owned npm graph unless a future change requires local packaging.
- Any dependency override or re-vendoring change must keep `npm run deps:tree`
  clean and preserve Task Master CLI and MCP smoke behavior.

## Required raw evidence after provider or dependency changes

Preserve raw output for:

- `npm ci`
- `npm ls`
- `npm audit --audit-level=moderate`
- `npx --yes --package task-master-ai@0.43.1 -c 'task-master models'`
- `npx --yes --package task-master-ai@0.43.1 -c 'task-master validate-dependencies'`
- `npx --yes --package task-master-ai@0.43.1 -c 'task-master next'`
- Task Master MCP startup when relevant

## Current repo rule

- Commit `.taskmaster/config.example.json`, not `.taskmaster/config.json`.
- Keep the local config cheap first: Ollama for default generation, Codex CLI
  only as explicit fallback or escalation.
- Keep telemetry and user-identity settings local and non-committed.
- Treat the PRD and committed task graph as repo artifacts; treat model/provider
  setup as operator-local runtime state.
