---
name: review
description: Use when conducting PR review, pre-merge review, security review, architecture review, or task-done validation.
---

# Review Skill

## Review checklist

- Task/PRD/ADR traceability.
- Correctness and edge cases.
- Server-side authorization.
- Database constraints and transactions.
- Tests and quality gates.
- Layering/import boundaries.
- Secrets and generated junk.
- Source-quality claims in docs, skills, and ADR changes.
- README/runbook updates where evaluator-facing behavior changed.

If the user explicitly asks for security best practices or threat modeling, use
the installed `$security-best-practices` or `$security-threat-model` skill in
addition to this review skill.

## Output

- Blocking issues:
- Non-blocking issues:
- Missing tests:
- Security concerns:
- Minimal fixes:
- Done recommendation:
