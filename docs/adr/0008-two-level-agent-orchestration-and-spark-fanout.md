# ADR-0008: Hybrid Direct-Specialist Orchestration With Spark Micro-Workers

- Status: accepted
- Date: 2026-06-14
- Deciders: Andrew Crozier

## Context

Library Ops needs a control plane that can route research, planning, command
summaries, UX work, Task Master recovery, and review without making the root
agent a bottleneck. The higher-risk part is recursive delegation: nested workers
can hide failures, duplicate edits, increase cost, and make final evidence more
difficult to audit.

The repo uses Spark micro-workers for the small, repeatable slices that benefit
from low-friction delegation: command execution, local evidence gathering, and
short source-backed research or summarization. The current posture keeps the
root as the only interactive coordinator while allowing explicitly assigned,
bounded depth-2 specialist chains when the root needs parallel coordination
support. The repo does not currently have reproducible evidence that unbounded
recursion or Spark-default planning improves this control plane enough to
justify the added complexity.

## Decision

Use direct-specialist routing as the active default, with Spark micro-workers
as the first stop for command and exploration slices:

- root coordinator uses `gpt-5.4-mini` with a 500,000-token effective input
  window and cost-aware default reasoning;
- `agents.max_depth = 2` for bounded specialist chains only;
- `agents.max_threads = 24`;
- root remains the only interactive coordinator and final decision owner;
- the root invokes specialists directly and only uses depth-2 delegation when
  the chain is explicitly bounded and assigned;
- `command_runner`, `context_gatherer`, `debugger`, `single_file_implementer`,
  `researcher`, and `docs_researcher` handle explicit commands, local
  exploration, failure triage, one-file fixes, and short evidence-backed
  lookups before the root expands scope;
- Task Master mutations route through `taskmaster_governor`;
- planning, research, and read-heavy specialists use `gpt-5.4-mini`.

## Alternatives considered

- Keep `max_depth = 2` with explicit bounded chains: lowest coordination risk
  for the current proven workflow while still allowing narrow follow-on
  specialists when the root must fan out deliberately.
- Unbounded nested agents: rejected because cost, latency, merge conflicts, and
  evidence loss would be hard to audit.
- Keep Spark as the default planner: rejected because Spark is better used for
  bounded command/exploration slices than for primary synthesis.

## Consequences

The package must validate the depth/thread cap, the active direct-specialist
workflow, and the Spark micro-worker routing rules. Any future recursion or
planner changes must be proven separately before they re-enter the committed
default path.

## Validation

- `codex doctor --summary --ascii --no-color`
- `npx --yes --package task-master-ai@0.43.1 -c 'task-master validate-dependencies'`
- `npm run eval:ci`
- smoke one command slice on `command_runner` and one exploration slice on
  `context_gatherer` or `researcher`, then record the observed routing in the
  current Task Master notes
