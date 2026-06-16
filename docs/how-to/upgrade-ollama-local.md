# Upgrade local Ollama on Linux/WSL2

Use this when the local control-plane works on smaller models but larger or
newer local models are still blocked by runtime behavior.

This upgrade is not required for the current smallest control-plane provider
lane if the local checks already pass. It becomes relevant when larger or newer
models are blocked by runtime behavior rather than by repo configuration.

## When to do this

Run this upgrade when all of these are true:

- the root-owned `ollama.service` is already in use for local workflows
- the current Ollama version is behind the current stable line
- a larger or newer local model is blocked by runtime behavior rather than missing auth

If the current local checks already succeed for the active provider lane, treat
the upgrade as an optimization step rather than an immediate requirement.

## Official update shape

Prefer the official Ollama Linux upgrade path:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

## Preserve systemd overrides

If the machine already depends on local GPU tuning, keep the existing systemd override or recreate it after the upgrade:

```ini
[Service]
Environment="CUDA_VISIBLE_DEVICES=0"
Environment="OLLAMA_DEBUG=INFO"
Environment="OLLAMA_VULKAN=0"
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_KV_CACHE_TYPE=q8_0"
```

## Post-upgrade commands

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
sudo systemctl status ollama --no-pager --full
ollama --version
ollama ps
```

## Required verification

Check the current scheduler and memory state before changing anything:

```bash
ollama ps
free -h
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader,nounits
journalctl -u ollama -n 120 --no-pager | rg -i 'evicting a model|truncating input prompt|total memory|kv cache|compute buffer|load request'
```

Interpretation rules:

- If multiple models are resident, clear them before benchmarking a new Task
  Master lane.
- If the logs show `truncating input prompt`, the configured context is too
  small for the current workload.
- If the logs show large CPU model/KV buffers, the model fits only by CPU
  offload and the tradeoff is speed rather than correctness.

Run all of these before changing repo-local model choices:

```bash
curl -sS http://127.0.0.1:11434/api/generate -d '{"model":"qwen2.5-coder:7b-instruct","prompt":"Return JSON only: {\"ok\":true}","stream":false}'
curl -sS http://127.0.0.1:11434/api/ps | python3 -m json.tool
journalctl -u ollama -n 120 --no-pager | rg -i 'gpu|cuda|cpu model buffer|cpu compute buffer|load failed|runner started'
```

Then rerun the exact local workflow that motivated the upgrade, for example:

```bash
npx --yes --package task-master-ai@0.43.1 -c 'task-master analyze-complexity --threshold=7'
npm run eval:provider:local
```

## Current Library Ops findings

- `qwen2.5-coder:3b` is cheap but too weak for reliable Task Master graph work.
- `deepcoder:1.5b` completes but still produces low-quality graph analysis.
- `qwen3.5:0.8b` fits comfortably but breaks structured-output reliability for Task
  Master.
- `qwen2.5-coder:7b-instruct` is the best proven local Task Master lane so far
  for bounded PRD parsing on this machine.
- `qwen3:latest` is the strongest already-proven local structured-output
  fallback candidate.
- DeepSeek variants are no longer the preferred local planning lane because the
  proven Qwen path is both cleaner and more reliable here.
- Remote providers such as `gemini-2.5-flash` remain rescue options, not the
  committed default local profile.
