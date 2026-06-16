# Run Promptfoo suites

Promptfoo is the primary control-plane eval layer for this repo.

The repo invokes Promptfoo through a version-pinned `npx` wrapper so evals stay
reproducible without carrying Promptfoo's full dependency tree inside the
project lockfile.

## Deterministic lane

Always run this first:

```bash
npm run eval:validate
npm run eval:smoke
npm run eval:ci
```

These checks must remain credential-free when possible.

## Provider-backed lane

Run only when a local provider is configured and approved:

```bash
npm run eval:provider:local
```

Or run a suite directly:

```bash
OLLAMA_BASE_URL=http://127.0.0.1:11434 npx --yes promptfoo@0.121.15 eval -j 1 -c evals/release/control-plane-provider.yaml --no-cache --output reports/validation/promptfoo-provider-local.json
```

The local Promptfoo judge does not need to be the same Ollama model used for
Task Master generation. Prefer the model that is most stable for the specific
assertion shape:

- Task Master generation uses the local task configuration under `.taskmaster/`.
- the committed local Promptfoo review lane stays on `qwen3.5:0.8b` because it
  is more reliable for this repo's strict JSON-only grading prompt.

Before trusting the provider-backed lane, verify the local provider itself:

```bash
ollama --version
ollama ps
curl -sS http://127.0.0.1:11434/api/generate -d '{"model":"qwen3.5:0.8b","prompt":"Return JSON only: {\"ok\":true}","stream":false}'
```

Use `-j 1` for the local provider lane so Promptfoo evaluates serially and only
keeps one local Ollama model active at a time. This improves repeatability on
smaller local machines.

## Reporting

If you keep a local run report, write `reports/validation/promptfoo-results.md` with:

- deterministic lane status;
- provider-backed lane status;
- red-team status;
- exact blockers when a lane is skipped or fails.

## Safety note

Promptfoo outputs can include config and provider information. Treat result files as local derived evidence, keep them out of git, and review them before sharing or relying on them in a final summary.
