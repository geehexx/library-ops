# Library Ops Constitution

## Purpose

This constitution governs the Library Ops interview demo. It exists to keep the
project predictable for humans, Codex, Task Master, Spec Kit, and any compatible
agent that later works in the repository.

Normative keywords `MUST`, `MUST NOT`, `SHOULD`, and `MAY` are used as binding
terms when uppercase.

## I. Requirements Before Implementation

All implementation work MUST trace to:

1. a section in `.taskmaster/docs/prd.md`,
2. a Task Master task or subtask,
3. and, when architecturally or procedurally significant, an ADR entry.

No feature work MAY begin from an informal prompt alone. If a prompt conflicts
with the PRD, the PRD MUST be updated or the conflict MUST be reported before
implementation proceeds.

## II. Single Source of Truth

`.taskmaster/docs/prd.md` is the canonical product, architecture, and execution
contract.

Spec Kit artifacts, generated Task Master tasks, README content, agent rules,
wireframes, runbooks, and supporting docs MUST derive from the PRD or explicitly
propose a PRD change before diverging.

Supporting docs SHOULD remain intentionally few. The project MUST avoid a sprawl
of overlapping PRDs, SRS documents, architecture documents, and test plans unless
the canonical PRD becomes too large to review.

When the canonical PRD is too large for a local-model operation, the project MAY
derive bounded phase PRDs under `.taskmaster/docs/phases/`, but those phase
views MUST remain derived artifacts rather than competing product truths.

## III. Domain Correctness

The system MUST distinguish:

- bibliographic work,
- edition or publication metadata,
- physical or logical copy,
- loan or circulation event,
- contributor/author metadata,
- source provenance for imported records.

The system MUST NOT model library inventory as a single `Book.status` field.
Borrowing operates on a copy. Historical loans MUST survive book archival.

## IV. Search Relevance Discipline

Search MUST prioritize exact identifiers before fuzzy, BM25, or semantic search.
The default ranking order is:

1. exact ISBN, barcode, Open Library ID, Gutenberg ID, or other external ID,
2. exact normalized title/contributor phrase,
3. PostgreSQL `tsvector` full-text search,
4. optional ParadeDB/BM25 adapter,
5. pgvector semantic similarity,
6. explicit business boosts and reciprocal-rank fusion.

Availability MUST be computed from database state, never from AI-generated text.
Semantic search MUST be additive, not authoritative.

## V. Security and Authorization

Privileged operations MUST enforce authorization server-side. UI hiding alone is
not authorization.

Secrets MUST NOT be committed. Real `.env`, `.mcp.json`, local Codex config,
model weights, corpora, local databases, and generated runtime state MUST remain
outside version control.

Demo credentials MAY be documented only when they are disposable and recreated by
seed commands.

## VI. Automated Quality Gates

Every pull request to `develop` or `main` MUST pass the applicable subset of:

- control-plane package hygiene checks,
- formatting,
- linting,
- static type checking,
- import-layer checks,
- Django system checks,
- migration checks,
- unit and integration tests,
- property-based tests for core invariants,
- E2E tests for user-critical flows once bootstraped.

Checks MAY be conditionally skipped only while their target bootstrap does not yet
exist, and the skip MUST be explicit in CI output.

## VII. Agent Compatibility

Codex is the primary implementation agent. The repository SHOULD remain usable by
other MCP-capable agents by keeping source-of-truth artifacts portable:

- `AGENTS.md`,
- `.taskmaster/docs/prd.md`,
- `.taskmaster/tasks/tasks.json`,
- `.specify/memory/constitution.md`,
- `.agents/skills/*/SKILL.md`,
- and conventional Markdown runbooks.

Agents MUST use Context7 or equivalent current documentation for framework/API
usage when implementation details are uncertain. Agents MAY use Exa or equivalent
web research for current external evidence. Figma MCP MAY be used for mockups,
but Markdown wireframes remain the repo-local design source.

Agent-operating context SHOULD live in AGENTS, skills, Codex config, or
repo-local references instead of being recreated under human-facing docs.

## VIII. Scope Discipline

The Valsoft assignment comes first:

- book management,
- borrow/return,
- search,
- runnable source code,
- README,
- product quality,
- usability.

Bonus features MAY be implemented only when they strengthen completeness,
creativity, product quality, usability, or engineering-management signal.

## IX. Decision Governance

An ADR entry is REQUIRED for decisions involving:

- framework or language choice,
- data model,
- search architecture,
- AI scope,
- authentication and authorization,
- deployment,
- SDLC and branch policy,
- quality gates,
- seed-data provenance,
- agent/MCP configuration,
- or documentation/source-of-truth structure.

## X. Reproducible Demo Data

Seed data MUST be generated by deterministic management commands, not by ad-hoc
manual database edits. Imports MUST track source provenance and license notes.
Commands SHOULD support `--dry-run`, `--limit`, and `--refresh` where practical.

## XI. Design Before Implementation

Core user flows SHOULD have repo-local wireframes before UI implementation. Figma
artifacts MAY be created from those wireframes, but the application MUST remain
implementable without relying on private Figma access.

## XII. Evidence, Research, and Claim Calibration

Material technical, product, deployment, security, and tooling claims MUST be
traceable to at least one of:

- a primary source recorded in the PRD source register,
- a relevant ADR, Task Master note, or current supporting reference such as
  `docs/reference/context-lineage.md`,
- a tool log or command output preserved in the implementation notes,
- or an explicitly marked assumption/open question.

Agents MUST NOT present a claim as verified when it was inferred, remembered, or
unavailable to the current tool session. Version-sensitive claims MUST be
rechecked during implementation.

Local-model recommendations MUST be backed by either a real bounded workflow
run or a repository-specific benchmark artifact. "Installed" is not evidence of
"fit for this repo."

## XIII. Connector and MCP Truthfulness

Agents MUST NOT claim to have used Exa, Context7, Figma, Task Master MCP, or any
other connector unless the session actually exposed and used that connector.
When a connector is unavailable, agents SHOULD use available official sources and
record that limitation. Repo configuration MAY prepare Codex to use MCPs later,
but configuration is not evidence of use.

## XIV. Deployment Demonstrability

The project MUST maintain an operational deployment path, not merely a codebase.
Before a release is evaluator-ready, the runbook and README MUST identify:

- deployment target and database target,
- required environment variables without secret values,
- migration and seed commands,
- static/media handling,
- smoke-test checklist,
- rollback or reset procedure,
- live URL and demo credentials when available.

## XV. Version Alignment

Documentation MUST stay aligned with dependency pins. If the project pins Django
5.2 LTS, implementation instructions SHOULD cite Django 5.2 documentation except
when comparing alternatives. Similar alignment applies to Python, PostgreSQL,
Task Master, Spec Kit, Codex, and MCP configuration.
