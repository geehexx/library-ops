# Use code-review-graph for review and blast-radius evidence

code-review-graph is part of the selected local code-intelligence stack. It does not replace direct source inspection, Serena symbol work, ast-grep structural search, or tests. It provides local graph and review-context evidence so agents can ask better blast-radius questions before editing or claiming correctness.

## Required local commands

```bash
npm run graph:build
npm run graph:status
npm run graph:review
```

If you keep graph evidence, capture it in:

```text
reports/validation/code-review-graph-review.md
reports/validation/logs/code-review-graph-build.log
reports/validation/logs/code-review-graph-status.log
reports/validation/logs/code-review-graph-review.log
```

If code-review-graph is missing, stale, or fails to build, record the exact blocker in current Task Master notes and any optional local `reports/validation/code-review-graph-review.md` output. Do not claim graph-backed review happened.

The npm commands are convenience wrappers around the verified repo-invoked
commands:

- `uvx --from code-review-graph code-review-graph build`
- `uvx --from code-review-graph code-review-graph status`

`graph:review` should capture a final combined transcript after those commands
succeed.

## MCP use

The Codex config exposes these code-review-graph MCP tools:

```text
query_graph_tool
semantic_search_nodes_tool
detect_changes_tool
get_review_context_tool
```

Use them for:

- blast-radius review of changed files
- identifying dependent modules and tests before broad edits
- finding review context for Django settings, models, services, tests, and agent-control files
- comparing graph output with Serena and direct source reads

Do not treat graph output as proof by itself. The report must name the files or areas inspected, the graph questions asked, and the tests or direct source checks that confirmed the result.

## Required report template

```markdown
# code-review-graph review

## Commands

| command | exit | log |
|---|---:|---|
| `npm run graph:build` | | `reports/validation/logs/code-review-graph-build.log` |
| `npm run graph:status` | | `reports/validation/logs/code-review-graph-status.log` |

## MCP / graph questions

- Question:
- Tool used:
- Result:
- Source files inspected afterward:
- Tests/checks affected:

## Blast-radius findings

- Changed area:
- Dependent modules/tests:
- Risk:
- Follow-up:
```
