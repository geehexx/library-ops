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
4. `.taskmaster/docs/phases/*.md` are derived PRD slices for local-model
   regeneration and benchmarking only; they do not replace the canonical PRD.

## Active MCP and companion-tool posture

- `TASK_MASTER_TOOLS=get_tasks,next_task,get_task,set_task_status,update_subtask,parse_prd`
  is the active default for Library Ops.
- We deliberately do **not** use `core`/`lean` as the repo default because the
  repo needs `parse_prd` inside the interactive loop, and we deliberately do
  **not** use `standard` as the repo default because the remaining standard
  tools are better handled through explicit CLI runs when their outputs are
  larger, slower, or more mutation-heavy.
- Keep in MCP:
  - `get_tasks`
  - `next_task`
  - `get_task`
  - `set_task_status`
  - `update_subtask`
  - `parse_prd`
- Repo-local required MCPs should stay `required = true` and
  `default_tools_approval_mode = "approve"` in `.codex/config.toml` so the
  coordinator can route the standard interactive toolchain without repeated
  approval churn.
- When shelling out to `npm` or `gh` from a sandboxed session, prefer
  `scripts/codex-runtime-env.sh` or an equivalent repo-local cache override so
  `npm_config_cache` and `XDG_CACHE_HOME` land under `TMPDIR` instead of a
  home-directory cache path.
- When running promptfoo locally, keep `PROMPTFOO_CONFIG_DIR` and
  `PROMPTFOO_LOG_DIR` under `TMPDIR` so the config database, WAL, and logs do
  not fall back to `~/.promptfoo`.
- Do not read `.taskmaster/state.json` directly; use the Task Master MCP or CLI
  and keep local runtime state out of the committed graph.
- Keep on CLI:
  - `analyze_project_complexity`
  - `complexity_report`
  - `expand_task`
  - `expand_all`
  - `add_task`
  - `add_subtask`
  - `remove_task`
  - `generate`
  - `models`
  - `research`
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

### Profile A: proven low-memory local generation profile

Use this when you need a bounded Task Master generation path that works locally
on the current machine without depending on a remote provider:

```json
{
  "models": {
    "main": {
      "provider": "ollama",
      "modelId": "qwen2.5-coder:7b-instruct",
      "maxTokens": 64000,
      "temperature": 0.1,
      "baseURL": "http://127.0.0.1:11434/api"
    },
    "research": {
      "provider": "ollama",
      "modelId": "qwen2.5-coder:7b-instruct",
      "maxTokens": 64000,
      "temperature": 0.1,
      "baseURL": "http://127.0.0.1:11434/api"
    },
    "fallback": {
      "provider": "ollama",
      "modelId": "qwen3:latest",
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
- local `qwen2.5-coder:7b-instruct` passed the repository-specific structured
  benchmark in both default and `/no_think` variants;
- local `qwen2.5-coder:7b-instruct` also completed a real
  `task-master parse-prd` run against
  `.taskmaster/docs/phases/phase-0-governance-and-foundation.md`, producing 4
  tasks in about 44 seconds with Ollama as the provider;
- local `qwen3:latest` passed the same repository-specific structured benchmark
  in both default and `/no_think` variants and is the strongest already-proven
  local fallback candidate for bounded structured generation;
- local `deepseek-r1:7b` and tool-calling derivatives remained weaker and
  noisier on the same structured Task Master planning rubric than the Qwen lane.

### Profile B: qwen3-first structured planning track

Use this when the task benefits from Qwen3's hybrid thinking/tool behavior and
you are willing to trade more CPU/RAM pressure for a richer local structured
planning pass:

```json
{
  "models": {
    "main": {
      "provider": "ollama",
      "modelId": "qwen3:latest",
      "maxTokens": 64000,
      "temperature": 0.1,
      "baseURL": "http://127.0.0.1:11434/api"
    },
    "research": {
      "provider": "ollama",
      "modelId": "qwen3:latest",
      "maxTokens": 64000,
      "temperature": 0.1,
      "baseURL": "http://127.0.0.1:11434/api"
    },
    "fallback": {
      "provider": "ollama",
      "modelId": "qwen2.5-coder:7b-instruct",
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
    "projectName": "Library Ops"
  }
}
```

Use this profile with an explicit optimization process:

1. keep only one Ollama model resident at a time;
2. avoid parallel heavy commands because current failure pressure is CPU/RAM as
   much as VRAM;
3. lower context before blaming the model;
4. use default Q4_K_M variants before heavier quantizations;
5. benchmark structured-output tasks and bounded Task Master operations, not
   just chat quality;
6. if the active local model violates JSON/schema constraints, fall back to the
   other proven Qwen local model before escalating off-box.

Observed on this machine:

- `qwen2.5-coder:7b-instruct` is currently the strongest practical local Task
  Master path because it has both structured-benchmark proof and real bounded
  `parse-prd` proof on this machine;
- `qwen3:latest` is slower and heavier on prompt handling, but it remains a
  high-quality local fallback with strong structured-output behavior;
- the earlier DeepSeek variants demonstrated that the remaining local blocker is
  not only VRAM pressure. CPU/RAM pressure and structured-output reliability
  under the Task Master prompt shape both matter.

## Ollama optimization process for this machine

Current observed machine facts:

- GPU: RTX 4050 Laptop GPU with about 6 GiB VRAM
- System RAM headroom can be tight when other work is running
- multiple concurrently resident models materially increase both VRAM pressure
  and host RAM/CPU pressure

Follow this process before declaring a local model unusable:

1. ensure only one model is loaded: use `ollama ps` and `ollama stop <model>`;
2. prefer strictly serial model tests and avoid overlapping benchmarking or
   generation runs;
3. prefer `OLLAMA_MAX_LOADED_MODELS=1` and `OLLAMA_NUM_PARALLEL=1` when sharing
   the machine with other workloads;
4. if needed, reduce `num_ctx` from 4096 to 2048 in a custom Modelfile or
   request options before concluding the model does not fit;
5. stay on Q4_K_M unless you have proven headroom for a higher-precision
   variant;
6. benchmark the exact Task Master operation you care about: complexity
   analysis, expansion, or PRD parsing;
7. inspect `ollama ps` after the run to verify the GPU/CPU split rather than
   guessing.

## Current provider findings

- `qwen2.5-coder:3b`: cheap and runnable, but low-quality on the live Task
  Master graph.
- `deepcoder:1.5b`: runnable and smaller, but still low-quality on graph
  analysis.
- `qwen3.5:0.8b`: fit comfortably, but produced malformed JSON for the Task
  Master structured-output path.
- `qwen2.5-coder:7b-instruct`: best proven local Task Master CLI lane so far
  for bounded PRD parsing on this machine.
- `qwen3:latest`: best already-proven local structured-output fallback, and the
  next candidate to test for a heavier end-to-end Task Master operation.
- `deepseek-r1:7b`: can run, but it is no longer the preferred local planning
  lane because the Qwen models have stronger current evidence on this machine.
- custom `deepseek-r1` 16k variants can remove prompt truncation, but on the
  current Task Master structured-output path they are slower and less reliable
  than the proven Qwen lane.
- `gemini-2.5-pro`: rate-limited on the current account.
- `gemini-2.5-flash`: useful off-box rescue lane when local providers cannot
  prove the needed operation, but no longer the committed default profile.
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

## MCP versus CLI routing

Use MCP for:

- task inspection during interactive runs;
- next-task lookup;
- task status updates;
- durable subtask notes;
- PRD parsing when the result is being actively reviewed in the same session.

Use CLI for:

- complexity analysis and reports;
- expansion work;
- graph regeneration experiments;
- bulk task mutations;
- model/provider tuning;
- any operation where you want raw stdout preserved as evidence.

## Phase-based local regeneration

When a local model is not yet reliable enough for the full canonical PRD,
prefer bounded phase PRDs:

- `phase-0-governance-and-foundation.md`
- `phase-1-bootstrap-domain-rbac.md`
- `phase-2-core-assignment-features.md`
- `phase-3-bonus-quality-features.md`
- `phase-4-deployment-and-demo.md`

This keeps the canonical PRD intact while giving local providers smaller,
phase-aligned generation targets.

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
