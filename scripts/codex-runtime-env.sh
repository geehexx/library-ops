#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -eq 0 ]; then
  echo "usage: bash scripts/codex-runtime-env.sh <command> [args...]" >&2
  exit 2
fi

RUNTIME_CACHE_ROOT="${TMPDIR:-/tmp}/library-ops-codex"

mkdir -p \
  "$RUNTIME_CACHE_ROOT/xdg-cache" \
  "$RUNTIME_CACHE_ROOT/npm-cache" \
  "$RUNTIME_CACHE_ROOT/pip-cache" \
  "$RUNTIME_CACHE_ROOT/promptfoo/cache" \
  "$RUNTIME_CACHE_ROOT/uv-cache" \
  "$RUNTIME_CACHE_ROOT/promptfoo/config" \
  "$RUNTIME_CACHE_ROOT/promptfoo/logs"

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
