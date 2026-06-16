# ADR-0008: Direct-Specialist Orchestration And Spark Lane Posture

- Status: accepted
- Date: 2026-06-14
- Deciders: root coordinator, user
- Supersedes: none

## Context

Library Ops needs a control plane that can route research, planning, command
summaries, UX work, Task Master recovery, and review without making the root
agent a bottleneck. The higher-risk part is recursive delegation: nested workers
can hide failures, duplicate edits, increase cost, and make final evidence more
difficult to audit.

The repo previously experimented with `agents.max_depth = 2` plus Spark-specific
agents. Current official Codex guidance keeps the default at `max_depth = 1`
unless deeper recursion is explicitly justified. The repo does not currently
have reproducible evidence that nested recursion improves this control plane
enough to justify the added complexity, but it does have evidence that direct
specialist routing works and that Spark may still be useful as an explicitly
invoked micro-worker lane.

## Decision

Use direct-specialist routing as the active default:

- root model uses `gpt-5.4` with a 1,000,000-token configured context target
  and cost-aware default reasoning;
- `agents.max_depth = 1`;
- `agents.max_threads = 8`;
- root remains the only interactive coordinator and final decision owner;
- the root invokes specialists directly instead of relying on recursive fan-out;
- Task Master mutations route through `taskmaster_governor`;
- planning, research, and read-heavy specialists use `gpt-5.4-mini`;
- Spark-named specialists may remain available for explicitly assigned
  text-only micro-work, but they are not evidence that recursive orchestration
  should be re-enabled by default.

## Alternatives considered

- Keep `max_depth = 1`: lowest coordination risk and the best match for the
  current proven workflow.
- Unbounded nested agents: rejected because cost, latency, merge conflicts, and
  evidence loss would be hard to audit.
- Remove Spark entirely: rejected because the user explicitly wants a cheap
  micro-worker lane available when it is helpful and bounded.

## Consequences

The package must validate the depth/thread cap, active direct-specialist
workflow, and any future Spark or recursion experiments separately from the
default path.

## Validation

- `codex doctor --summary --ascii --no-color`
- `npx --yes --package task-master-ai@0.43.1 -c 'task-master validate-dependencies'`
- `npm run eval:ci`
- current Task Master notes or temporary local validation output summarizing the
  direct-specialist workflow and any later Spark experiment
