# LearnedPatterns.md

> Patterns extracted from past work. Referenced when starting new tasks
> (CommonClaude §9).

## §1. Recurring Issues

## §2. Solved Gotchas

## §3. Library Quirks

### jq on Windows emits CRLF
- **Problem**: `jq -r` output on Windows ends with `\r\n`.
- **Cause**: The Windows `jq` build writes text-mode line endings.
- **Fix**: Git Bash strips the CR inside `$(...)`; pipe through
  `tr -d '\r'` anywhere else the output is consumed raw.
- **Rule**: Always strip `\r` from `jq` output outside command
  substitution on Windows. (from ToDo#1)

## §4. Workflow Lessons

## §5. Environment Specifics

### Shared hook scripts checked out with CRLF
- **Problem**: CommonClaude hooks fail under bash on Windows.
- **Cause**: `core.autocrlf=true` converts `*.sh` to CRLF on checkout.
- **Fix**: `run-common-hook.sh` runs the hook via
  `bash <(tr -d '\r' < hook)`; `.gitattributes` pins `*.sh` to LF.
- **Rule**: Never run a submodule shell script on Windows without
  stripping CR first. (from ToDo#1)

### Backslash paths bypass shared hook globs
- **Problem**: `pre-write-guard` and `post-write-debug-remind` let
  `C:\proj\tests\debug_x.py` through silently.
- **Cause**: The hooks match `*/tests/*`, but Windows tool payloads can
  carry `\` separators.
- **Fix**: The wrapper rewrites `tool_input.file_path` to `/` with `jq`
  before calling the shared hook.
- **Rule**: Always test hooks with both `/` and `\` paths on Windows.
  (from ToDo#1)

### winget PATH changes need a restart
- **Problem**: `jq` installed via winget is not found by running tools.
- **Cause**: winget edits the user `PATH`; already-running processes
  (VS Code, Claude Code) keep the old environment.
- **Fix**: Restart VS Code after installing hook dependencies.
- **Rule**: Always restart the editor after installing a hook
  dependency. (from ToDo#1)

## §99. Uncategorized
