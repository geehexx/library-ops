#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

rm -rf reports
rm -rf .taskmaster/reports

# Remove empty placeholder directories that are left behind after pruning local outputs.
find docs -type d -empty -delete 2>/dev/null || true
find . -path ./.git -prune -o -type d -empty -delete 2>/dev/null || true

printf 'Removed transient local artifacts from %s\n' "$repo_root"
