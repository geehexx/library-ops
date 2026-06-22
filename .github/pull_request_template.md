## Task Master

- Task ID:
- Task title:
- Dependencies satisfied:

## PRD / Spec Kit / ADR traceability

- PRD section:
- Spec Kit artifacts changed or referenced:
- ADRs changed or referenced:
- Decision status / user tie-back:
- Alternatives and counterfactual evidence for material tooling/scope/architecture changes:

## Change summary

## Required-tool evidence

- RTK used for noisy output:
- Raw reruns/full logs captured where required:
- code-review-graph evidence:
- Serena evidence:
- ast-grep evidence:
- Repomix evidence if used:
- Context7/Exa/Figma/Task Master MCP usage recorded:
- New trust/cost/credential/scope decision introduced:

## Screenshots / evaluator evidence

## Tests

- [ ] Unit tests
- [ ] Integration tests
- [ ] Property-based tests
- [ ] E2E tests
- [ ] Manual smoke test

## Quality gates

- [ ] `npm run checks:precommit`
- [ ] `codex doctor --summary --ascii --no-color`
- [ ] `npm run taskmaster:validate`
- [ ] `npm run deps:tree`
- [ ] `npm run skills:lint`
- [ ] `npm run release:check`
- [ ] `npm run workflow:lint`
- [ ] `npm run policy:check`
- [ ] `npm run security:scan`
- [ ] `uv run ruff format --check .`
- [ ] `uv run ruff check .`
- [ ] `uv run pyright`
- [ ] `uv run lint-imports`
- [ ] `uv run pytest`
- [ ] `uv run python manage.py makemigrations --check --dry-run`
- [ ] `gitleaks detect --source . --redact`
- [ ] `semgrep scan --config .semgrep.yml`
- [ ] `uv run pip-audit --progress-spinner off`
- [ ] `actionlint`
- [ ] `zizmor .`
- [ ] `conftest test .codex/config.toml --policy policy`
- [ ] `npm run markdownlint`
- [ ] `npm audit --audit-level=moderate`
- [ ] `npm run checks:prepush` (authoritative local pre-push gate)

## Self-review

- [ ] I reviewed the diff line by line.
- [ ] I checked authorization boundaries.
- [ ] I checked architecture approach, domain boundaries, and import boundaries.
- [ ] I checked migrations.
- [ ] I checked no secrets or generated junk were added.
- [ ] I did not treat filtered/graph/symbol output as proof without source/test inspection.
- [ ] I updated Task Master status/notes.
- [ ] I updated README/docs where evaluator-facing behavior changed.
- [ ] I ran or recorded the required-tooling check.
- [ ] I ran a retrospective or explained why it was unnecessary.
