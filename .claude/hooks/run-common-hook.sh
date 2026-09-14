#!/bin/bash
# Run a shared CommonClaude hook from the submodule with Windows-safe
# input. Usage: run-common-hook.sh <hook-script-name>
#
# Two Windows-only problems are patched here rather than in the
# submodule, so the shared scripts stay identical to upstream:
# 1. Claude Code passes backslash paths (C:\proj\tests\x.py), but the
#    shared hooks match forward-slash globs such as */tests/*.
# 2. With core.autocrlf=true the scripts are checked out with CRLF,
#    which bash refuses to run.
set -euo pipefail

hook_name="$1"
script_dir=$(cd "$(dirname "$0")" && pwd)
repo_root="${CLAUDE_PROJECT_DIR:-$script_dir/../..}"
hook_path="$repo_root/external/CommonClaude/.claude/hooks/$hook_name"

if [[ ! -f "$hook_path" ]]; then
    echo "WARNING: shared hook not found: $hook_path" >&2
    echo "Run: git submodule update --init --recursive" >&2
    exit 0
fi

if ! command -v jq &>/dev/null; then
    echo "WARNING: jq is not installed; $hook_name skipped." >&2
    echo "Install with: winget install jqlang.jq" >&2
    exit 0
fi

input=$(cat)
normalized=$(
    printf '%s' "$input" \
        | jq -c '
            if .tool_input.file_path? then
                .tool_input.file_path |= gsub("\\\\"; "/")
            else . end' \
        | tr -d '\r'
)

printf '%s' "$normalized" | bash <(tr -d '\r' < "$hook_path")
