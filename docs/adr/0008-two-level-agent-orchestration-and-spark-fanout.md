# ADR-0008: Direct-Specialist Orchestration Without A Spark Default Lane

- Status: accepted
- Date: 2026-06-14
- Deciders: Andrew Crozier

## Context

Library Ops needs a control plane that can route research, planning, command
summaries, UX work, Task Master recovery, and review without making the root
agent a bottleneck. The higher-risk part is recursive delegation: nested workers
can hide failures, duplicate edits, increase cost, and make final evidence more
difficult to audit.

The repo previously experimented with `agents.max_depth = 2` plus Spark-specific
agents. The current committed posture keeps the root as the only interactive
coordinator while allowing explicitly assigned, bounded depth-2 specialist
chains when the root needs parallel coordination support. The repo does not
currently have reproducible evidence that unbounded recursion or Spark-specific
routing improves this control plane enough to justify the added complexity.

## Decision

Use direct-specialist routing as the active default:

- root model uses `gpt-5.4` with a 1,000,000-token configured context target
  and cost-aware default reasoning;
- `agents.max_depth = 2` for bounded specialist chains only;
- `agents.max_threads = 12`;
- root remains the only interactive coordinator and final decision owner;
- the root invokes specialists directly and only uses depth-2 delegation when
  the chain is explicitly bounded and assigned;
- Task Master mutations route through `taskmaster_governor`;
- planning, research, and read-heavy specialists use `gpt-5.4-mini`.

## Alternatives considered

- Keep `max_depth = 2` with explicit bounded chains: lowest coordination risk
  for the current proven workflow while still allowing narrow follow-on
  specialists when the root must fan out deliberately.
- Unbounded nested agents: rejected because cost, latency, merge conflicts, and
  evidence loss would be hard to audit.
- Keep Spark-specific lanes in the committed default: rejected because the repo
  does not currently have reproducible operational proof for them.

## Consequences

The package must validate the depth/thread cap and active direct-specialist
workflow. Any future Spark or recursion experiment must be proven separately
before it re-enters the committed default path.

## Validation

- `codex doctor --summary --ascii --no-color`
- `npx --yes --package task-master-ai@0.43.1 -c 'task-master validate-dependencies'`
- `npm run eval:ci`
- current Task Master notes or temporary local validation output summarizing the
  direct-specialist workflow and any later experiment
