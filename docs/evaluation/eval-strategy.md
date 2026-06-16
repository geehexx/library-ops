# Evaluation strategy

Promptfoo is the primary Library Ops control-plane and AI-behavior evaluation system. Keep generic prompt/eval mechanics in Promptfoo configs and skills; avoid rebuilding evaluation logic in custom repo wrappers. The repo invokes Promptfoo as a version-pinned external CLI through `npx`, not as a repo-owned dependency.

## Lanes

| Lane | Command | Purpose | Credentials |
|---|---|---|---|
| Config | `npm run eval:validate` | Validate Promptfoo config syntax and schema. | None. |
| Deterministic smoke | `npm run eval:smoke` | Check control-plane wording, artifact policy, local-only config posture, and no-secret contracts with the `echo` provider. Writes a local ignored result under `reports/validation/`. | None. |
| CI aggregate | `npm run eval:ci` | Run config plus deterministic smoke. | None. |
| Provider semantic | `OLLAMA_BASE_URL=http://127.0.0.1:11434 npx --yes promptfoo@0.121.15 eval -j 1 -c evals/release/<suite>.yaml --no-cache --output reports/validation/promptfoo-<suite>.json` | Compare provider/model behavior after local provider setup succeeds. Outputs stay local under ignored `reports/validation/`. | Local/user-approved only. |
| Red-team | `npx --yes promptfoo@0.121.15 redteam init`, `npx --yes promptfoo@0.121.15 redteam run`, `npx --yes promptfoo@0.121.15 redteam report` | Probe prompt-injection, unsafe tool use, RBAC, data exfiltration, and policy bypass after the app boundary exists. | Local/user-approved only. |

## Current deterministic smoke scope

`promptfooconfig.yaml` and `evals/control-plane/prompt-contract.md` cover:

- source-of-truth order;
- Question packet, Escalation packet, `/goal`, and validation evidence;
- canonical, derived, and operator-local artifact classes;
- Task Master `.taskmaster/config.json` local-only posture;
- committed derived Task Master graph posture for `.taskmaster/tasks/tasks.json`;
- local-export exclusions for `.env*`, `.mcp.json`, OAuth tokens, provider keys, caches, generated corpora, and previous archives;
- direct-tool verification language for current repo state.

Do not treat repo docs as proof that a provider-backed lane passed recently.
Provider-backed runs are session-specific and should be captured in current Task
Master notes plus optional local `reports/validation/` outputs.

## Authoring rules

- Prefer deterministic assertions such as `contains`, `not-contains`, `equals`, `is-json`, `javascript`, or `python` before model-graded assertions.
- Use Promptfoo Nunjucks environment syntax such as `{{env.OPENAI_API_KEY}}`; do not write shell-style `$OPENAI_API_KEY` in YAML configs.
- Move larger prompts and test cases into files under `evals/` and reference them with `file://`.
- Store real provider credentials in local environment, CI secrets, user-level tool config, or approved MCP env blocks only.
- Record command, provider, model, exit code, output path, and failure triage in Task Master notes. Keep any `reports/validation/` output local and ignored unless a future curated artifact is explicitly approved.

## Red-team readiness criteria

Do not run broad red-team scans until the target boundary is clear. A red-team plan must identify:

1. target command, HTTP endpoint, or provider wrapper;
2. user inputs and authentication context;
3. allowed and forbidden tool actions;
4. protected data classes;
5. plugins/strategies selected and why;
6. narrow rerun command for failed probes.

## Secondary tools

DeepEval, Braintrust, LangSmith, and OpenAI Evals are not selected as primary gates. They may be benchmarked only if Promptfoo cannot express a needed behavior or if the project needs vendor-specific tracing/reporting later.

## Concrete examples

See `docs/evaluation/promptfoo-examples.md` for runnable patterns and `evals/redteam/control-plane-redteam.template.yaml` for the dormant red-team template.
