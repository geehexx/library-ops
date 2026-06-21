---
name: github-governance
description: Use when configuring GitHub repo, branch protections, PR template, CI, commitlint, CODEOWNERS, or release controls.
---

# GitHub Governance Skill

## Required controls

- `main` and `development` protected.
- PR required.
- Required status checks.
- Conversation resolution.
- CODEOWNERS review when applicable.
- Conventional Commits enforced.
- No force push/delete on protected branches.
- Prefer durable GitHub UI/admin configuration over repo helper scripts for branch protection.
- Keep GitHub Actions pinned to commit SHAs unless an explicit exception is accepted and documented.

If the task is specifically about diagnosing or fixing failing GitHub Actions
checks, use the installed `$gh-fix-ci` skill alongside this one. If the task is
about addressing PR review threads or inline GitHub comments, use the
installed `$gh-address-comments` skill alongside this one.

## Output

- GitHub command/manual step:
- Protection impact:
- Required checks:
- Follow-up verification:
