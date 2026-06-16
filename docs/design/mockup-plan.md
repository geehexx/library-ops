---
id: DESIGN-MOCKUP-PLAN-001
title: Evaluator Mockup Plan
status: accepted
updated: 2026-06-14
---

# Evaluator Mockup Plan

## Purpose

This plan defines the low-fidelity mockup set for the Library Ops evaluator
flow. It is repo-local so implementation can proceed without private design-tool
access.

## Frames

| Frame | Purpose | Primary states |
|---|---|---|
| Evaluator landing | Show assignment coverage and route quickly to catalog/login. | Ready, feature unavailable, deployment evidence missing. |
| Login and demo access | Demonstrate role-aware entry without committing real credentials. | Empty, invalid credentials, seeded demo password placeholder. |
| Catalog search | Prove exact search, filters, result explanation, and role actions. | Empty query, results, no results, degraded semantic search. |
| Book detail and copies | Show metadata, availability, copy status, audit trail, and checkout affordances. | Available, all copies loaned, archived, permission denied. |
| Circulation panel | Exercise checkout, return, renew, overdue feedback, and transactional errors. | Success, copy unavailable, member blocked, validation error. |
| Admin/librarian dashboard | Summarize collection, active loans, overdue items, imports, and quality evidence. | Normal, import running, import failed, no seed data. |
| AI metadata review | Keep AI assistance human-reviewed and provenance-backed. | Suggestions available, rejected suggestion, provider unavailable. |

## Implementation Constraints

- Use Django templates with small HTMX enhancements.
- Make role-aware affordances visible, but enforce authorization server-side.
- Include empty, error, loading, and permission-denied states for every major
  workflow.
- Prefer compact operational UI over marketing layout.
- Keep all demo credential values as placeholders produced by seed commands.

## Acceptance Checks

- Wireframes cover all PRD evaluator workflows.
- Each frame has a clear purpose, primary action, empty state, error state, and
  accessibility note.
- Wireframe dogfooding result is summarized in Task Master notes or a temporary
  local report, not committed as durable repo truth.
