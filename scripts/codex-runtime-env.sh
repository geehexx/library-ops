#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -eq 0 ]; then
  echo "usage: bash scripts/codex-runtime-env.sh <command> [args...]" >&2
  exit 2
fi

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"

prepare_runtime_cache_root() {
  local runtime_cache_root="$1"

  mkdir -p \
    "$runtime_cache_root/xdg-cache" \
    "$runtime_cache_root/npm-cache" \
    "$runtime_cache_root/pip-cache" \
    "$runtime_cache_root/promptfoo/cache" \
    "$runtime_cache_root/uv-cache" \
    "$runtime_cache_root/promptfoo/config" \
    "$runtime_cache_root/promptfoo/logs"
}

choose_runtime_cache_root() {
  local preferred_root="${TMPDIR:-/tmp}/library-ops-codex"
  local fallback_root="$REPO_ROOT/.codex/.tmp/library-ops-codex"

  if prepare_runtime_cache_root "$preferred_root" 2>/dev/null; then
    printf '%s\n' "$preferred_root"
    return 0
  fi

  prepare_runtime_cache_root "$fallback_root"
  printf '%s\n' "$fallback_root"
}

RUNTIME_CACHE_ROOT="$(choose_runtime_cache_root)"

export XDG_CACHE_HOME="$RUNTIME_CACHE_ROOT/xdg-cache"
export npm_config_cache="$RUNTIME_CACHE_ROOT/npm-cache"
export PIP_CACHE_DIR="$RUNTIME_CACHE_ROOT/pip-cache"
export PROMPTFOO_CACHE_PATH="$RUNTIME_CACHE_ROOT/promptfoo/cache"
export UV_CACHE_DIR="$RUNTIME_CACHE_ROOT/uv-cache"
export PROMPTFOO_CONFIG_DIR="$RUNTIME_CACHE_ROOT/promptfoo/config"
export PROMPTFOO_LOG_DIR="$RUNTIME_CACHE_ROOT/promptfoo/logs"

PLAYWRIGHT_BROWSER_ROOT="${PLAYWRIGHT_BROWSERS_PATH:-${HOME:-/tmp}/.cache/ms-playwright}"
if [ -d "$PLAYWRIGHT_BROWSER_ROOT" ]; then
  export PLAYWRIGHT_BROWSERS_PATH="$PLAYWRIGHT_BROWSER_ROOT"
fi

exec "$@"
