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

## Active MCP and companion-tool posture

- `TASK_MASTER_TOOLS=standard` is the active default for Library Ops.
- We deliberately do **not** use `core`/`lean` as the repo default because the
  current control-plane workflow routinely needs:
  - `analyze_project_complexity`
  - `complexity_report`
  - `expand_all`
  - `add_task`
  - `add_subtask`
  - `remove_task`
- Treat Task Master as one part of a larger graph-governance tool bundle:
  - Context7 for version-specific framework/provider docs
  - Exa for broader current research and counter-evidence
  - Serena for symbol-aware repo alignment
  - code-review-graph for blast radius and test impact

These companion tools should already be available through the project Codex
config when `codex doctor --summary --ascii --no-color` is healthy. They do not
require separate per-run activation. Serena's server starts from the current
working directory via `.codex/config.toml`; using its `activate_project` tool is
 for symbol-aware work, not a prerequisite for ordinary Task Master operations.

## Recommended local profiles

### Profile A: recommended working graph-management profile

Use this when you need Task Master graph operations to work reliably on the
current machine and current account state:

```json
{
  "models": {
    "main": {
      "provider": "gemini-cli",
      "modelId": "gemini-2.5-flash",
      "maxTokens": 64000,
      "temperature": 0.1
    },
    "research": {
      "provider": "gemini-cli",
      "modelId": "gemini-2.5-flash",
      "maxTokens": 128000,
      "temperature": 0.1
    },
    "fallback": {
      "provider": "ollama",
      "modelId": "deepseek-r1:7b",
      "maxTokens": 64000,
      "temperature": 0.1,
      "baseURL": "http://127.0.0.1:11434/api"
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

Evidence behind this recommendation:

- local `qwen2.5-coder:3b` returned materially wrong complexity analyses for the
  live graph;
- local `deepcoder:1.5b` completed but still produced incorrect task identity;
- local `qwen3.5:0.8b` generated malformed JSON for the Task Master schema path;
- local `deepseek-r1:7b` can run on this class of hardware, but on the current
  Task Master structured-output path it still needed a fallback rescue;
- `gemini-2.5-flash` produced the first correct Task 3 analysis on this machine
  and account state;
- `codex-cli` fallback models `gpt-5.4-mini` and `gpt-5.2-codex` were both
  rejected by the current installed Codex/account combination.

### Profile B: local-first experimental optimization track

Use this when you want to improve the local Ollama lane rather than default to
the proven Gemini path:

```json
{
  "models": {
    "main": {
      "provider": "ollama",
      "modelId": "deepseek-r1:7b",
      "maxTokens": 64000,
      "temperature": 0.1
    },
    "research": {
      "provider": "ollama",
      "modelId": "deepseek-r1:7b",
      "maxTokens": 64000,
      "temperature": 0.1
    },
    "fallback": {
      "provider": "gemini-cli",
      "modelId": "gemini-2.5-flash",
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

Use this profile with an explicit optimization process:

1. keep only one Ollama model resident at a time;
2. lower context before blaming the model;
3. use default Q4_K_M variants before heavier quantizations;
4. benchmark structured-output tasks, not just chat quality;
5. if the local model violates JSON/schema constraints, let Gemini Flash rescue
   the run and treat the local lane as still unproven.

Observed on this machine:

- the stock `deepseek-r1:7b` 4k context path fit in memory but truncated a
  ~14k-token Task Master prompt to 4096 tokens before answering;
- a custom 16k-context `deepseek-r1` variant removed truncation and still fit
  by moving more weights and KV cache to CPU, but the run took nearly three
  minutes and still failed the Task Master structured-output schema;
- the remaining blocker is therefore not only memory pressure. It is also
  structured-output reliability under the Task Master prompt shape.

## Ollama optimization process for this machine

Current observed machine facts:

- GPU: RTX 4050 Laptop GPU with about 6 GiB VRAM
- System RAM headroom can be tight when other work is running
- multiple concurrently resident models materially increase VRAM pressure

Follow this process before declaring a local model unusable:

1. ensure only one model is loaded: use `ollama ps` and `ollama stop <model>`;
2. prefer `OLLAMA_MAX_LOADED_MODELS=1` and `OLLAMA_NUM_PARALLEL=1` when sharing
   VRAM with other workloads;
3. if needed, reduce `num_ctx` from 4096 to 2048 in a custom Modelfile or
   request options before concluding the model does not fit;
4. stay on Q4_K_M unless you have proven VRAM headroom for a higher-precision
   variant;
5. benchmark the exact Task Master operation you care about: complexity
   analysis, expansion, or PRD parsing;
6. inspect `ollama ps` after the run to verify the GPU/CPU split rather than
   guessing.

## Current provider findings

- `qwen2.5-coder:3b`: cheap and runnable, but low-quality on the live Task
  Master graph.
- `deepcoder:1.5b`: runnable and smaller, but still low-quality on graph
  analysis.
- `qwen3.5:0.8b`: fit comfortably, but produced malformed JSON for the Task
  Master structured-output path.
- `qwen2.5-coder:7b-instruct`: hit VRAM OOM under current shared-load
  conditions; retry only after serializing model residency and, if needed,
  lowering context.
- `deepseek-r1:7b`: promising local reasoning candidate; keep optimizing and
  benchmarking it, but do not yet treat it as the sole reliable graph lane.
- custom `deepseek-r1` 16k variants can remove prompt truncation, but on the
  current Task Master structured-output path they are still slower and not yet
  schema-reliable enough to replace Gemini Flash.
- `gemini-2.5-pro`: rate-limited on the current account.
- `gemini-2.5-flash`: currently the best proven Task Master graph-management
  lane on this machine/account.
- `codex-cli gpt-5.4-mini`: rejected because the installed Codex CLI is too old
  for that model.
- `codex-cli gpt-5.2-codex`: rejected on the current ChatGPT-backed account.

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
- Keep the committed example on the best currently proven working provider path,
  and treat local Ollama optimization as an explicit tuning track backed by
  repeated benchmark evidence.
- Keep telemetry and user-identity settings local and non-committed.
- Treat the PRD and committed task graph as repo artifacts; treat model/provider
  setup as operator-local runtime state.
