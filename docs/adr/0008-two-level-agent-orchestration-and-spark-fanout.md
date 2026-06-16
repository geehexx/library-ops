# ADR-0008: Two-Level Agent Orchestration And Spark Fan-Out

- Status: accepted
- Date: 2026-06-14
- Deciders: root coordinator, user
- Supersedes: none

## Context

Library Ops needs a control plane that can fan out research, planning, command
summaries, UX work, Task Master recovery, and review without making the root
agent a bottleneck. The first remediation passes kept `agents.max_depth = 1`
because nested delegation can hide failures, duplicate edits, increase cost, and
make final evidence more difficult to audit.

The user explicitly selected a two-level pilot and asked for Spark agents to be
available to both the root and lead agents. Earlier remediation passes treated
Spark as too unstable for the fast path and substituted `gpt-5.4-mini`
instead. Current official Codex guidance still distinguishes three lanes, and
the user wants the cost-aware one: keep `gpt-5.4` as the large-context
default, use `gpt-5.4-mini` for read-heavy planning and exploration, and keep
`gpt-5.3-codex-spark` only for near-instant text-only micro-work.

## Decision

Enable a controlled depth-2 pilot:

- root model uses `gpt-5.4` with a 1,000,000-token configured context target
  and cost-aware default reasoning;
- `agents.max_depth = 2`;
- `agents.max_threads = 8`;
- root remains the only interactive coordinator and final decision owner;
- lead agents may coordinate one granular layer only when the root has defined
  scope, ownership, runtime cap, upward summary, and validation;
- Task Master mutations route through `taskmaster_governor`;
- planning, research, and read-heavy specialists use `gpt-5.4-mini`;
- Spark-named specialists may summarize commands, community sources, and noisy
  evidence, backed by `gpt-5.3-codex-spark`, but raw commands remain
  authoritative for final validation.

## Alternatives considered

- Keep `max_depth = 1`: lowest coordination risk, but does not dogfood the
  intended second-level orchestration system.
- Unbounded nested agents: rejected because cost, latency, merge conflicts, and
  evidence loss would be hard to audit.
- Make the older Spark preview model the default command runner: rejected;
  Spark remains useful, but only as a bounded text-only micro-worker.

## Consequences

The package must validate the depth/thread cap, agent files, explicit
mini-backed planning lanes, Spark-backed text-only lanes, and dogfooding
evidence. Reports must record elapsed time, agents used, blockers, and whether
nested coordination improved or harmed the run.

## Validation

- `codex doctor --summary --ascii --no-color`
- `npx --yes --package task-master-ai@0.43.1 -c 'task-master validate-dependencies'`
- `npm run eval:ci`
- current Task Master notes or temporary local validation output summarizing the dogfooding run
