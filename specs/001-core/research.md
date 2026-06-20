# Research Summary

## Architecture

Use C4-style views for communication, arc42-style quality/risk framing, and pragmatic domain boundaries. Full tactical DDD and microservices are rejected for the MVP because they add ceremony and deployment burden. Django service/selector layering gives enough boundary clarity while staying idiomatic, and presentation ownership should live with the relevant Django apps rather than a monolithic shell or other bad anchor surface.

## Tooling

The implementation environment requires Codex CLI, Task Master, Spec Kit, RTK, code-review-graph, Serena, ast-grep, Repomix, agent-skills-lint, Gitleaks, Semgrep, pip-audit, npm audit, actionlint, zizmor, and Conftest. Hosted/cloud code-indexing and paid dashboards are deferred until explicit user approval.

## Search

Exact identifier ranking is mandatory. PostgreSQL full-text search is the current lexical baseline, with SQLite-safe fallback behavior where needed for local tests. ParadeDB/BM25 and semantic/vector layers are out of the current release scope. Test strategy should stay kind-first: lower-level invariants before request and browser coverage.

## Data provenance

Public-domain imports must record source, license notes, identifiers, import batch, and refresh behavior. AI-assisted metadata is not in the current release scope; if it returns later, it must come back through a new PRD/task slice with explicit provenance rules.

## Evidence sources

Detailed source-backed evidence belongs in the PRD source register, the active
ADRs, and current task notes rather than separate historical evidence files.
