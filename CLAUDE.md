# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working
with code in this repository.

## Common Conventions

This repository adopts the shared **CommonClaude** harness, vendored as a
git submodule at `external/CommonClaude`. Its ruleset applies in full:

@external/CommonClaude/CLAUDE.md

Per CommonClaude §1 Rule Priority, the project-specific rules below take
precedence wherever they conflict with the shared ruleset.

---

## Project Overview

SpincoaterAutomation automates a laboratory spin coater.

<!-- TODO: (@coport-uni) Describe the device model, control interface,
     and project scope once they are fixed. -->

## Repository Layout

| Path                    | Purpose                                            |
|-------------------------|----------------------------------------------------|
| `docs/`                 | Reference material (manuals, datasheets, notes).   |
| `external/CommonClaude` | Shared harness submodule. **Do not edit in place.** |
| `.claude/`              | Project hook wiring that points into the submodule. |
| `claude_test/`          | Debug and exploratory scripts (CommonClaude §3).   |
| `tests/`                | Production-quality tests (CommonClaude §3).        |

## Environment (overrides CommonClaude "Environment")

This project is developed **natively on Windows 11**, not in the Docker
container described by CommonClaude.

| Item     | Detail                                                  |
|----------|---------------------------------------------------------|
| OS       | Windows 11                                              |
| Shell    | PowerShell 5.1 and Git Bash                             |
| Dev tool | Claude Code (VS Code extension)                         |
| Hooks    | Run through Git Bash; require `jq` and `ruff` on `PATH` |

Install the hook dependencies with:

```powershell
winget install jqlang.jq
pip install ruff
```

## Harness Submodule

- The hook scripts are executed **from the submodule**
  (`external/CommonClaude/.claude/hooks/`). `.claude/settings.json` wires
  each one through `.claude/hooks/run-common-hook.sh`, which patches two
  Windows problems without touching the shared scripts:
  - backslash paths are rewritten to `/`, so globs like `*/tests/*` match;
  - CR characters are stripped, so CRLF checkouts
    (`core.autocrlf=true`) still run under bash.
- After cloning, fetch the submodule:
  `git submodule update --init --recursive`
- To adopt upstream rule changes, bump the pointer on a working branch:
  `git submodule update --remote external/CommonClaude`, then commit as
  `chore(harness): bump CommonClaude`.
- Change shared rules **upstream** in `coport-uni/CommonClaude`, never
  inside `external/CommonClaude`. Project-only rules belong in this file.

## Hardware Safety

A spin coater drives a high-speed spindle, so every change to device
control code falls under the CommonClaude §5.1 Verification Gate: run it on
the real device with the operator present before any commit, and never
start rotation on your own initiative.
