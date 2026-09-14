# ToDo

## Apply CommonClaude harness

### Background
User request (2026-09-14): add `coport-uni/CommonClaude` as a git
submodule and apply its Claude Code harness to this repository.
Reference: https://github.com/coport-uni/CommonClaude

### Decisions (2026-09-14)
- Submodule path: `external/CommonClaude` (tracks `main`)
- Rules: root `CLAUDE.md` imports `@external/CommonClaude/CLAUDE.md` and
  adds project overrides (Windows host instead of Docker)
- Hooks: root `.claude/settings.json` runs the scripts straight from the
  submodule, so upstream hook fixes arrive with a pointer bump
- Language profile: Python (`main` branch of CommonClaude, Ruff)
- Windows fixes live in project wrapper `.claude/hooks/run-common-hook.sh`
  (backslash path normalization, CR stripping); submodule stays untouched
  (see LP §5)

### Tasks
- [x] Initialize git repository (`main`)
- [x] Add submodule `external/CommonClaude`
- [x] Install hook dependency `jq` via winget
- [x] Write root `CLAUDE.md` with import and project overrides
- [x] Write root `.claude/settings.json` wiring submodule hooks
- [x] Add `.gitignore` (CommonClaude §13.1), `pyproject.toml` (Ruff, §6)
- [x] Add `.gitattributes` forcing LF on `*.sh`
- [x] Add `claude_test/README.md` index (§3)
- [x] Write `.claude/hooks/run-common-hook.sh` Windows wrapper
- [x] Verify each hook with sample tool payloads on Windows Git Bash
  (15/15 cases pass: fwd/backslash paths, secrets, CRLF, missing jq)
- [ ] Install `ruff` (no real Python interpreter on host yet)
- [x] Create GitHub repository `coport-uni/SpinCoaterAutomation`
  (done by user)
- [x] Initial commit and push (a924380, done by user)
- [x] Create GitHub issue for this task (#1)
- [ ] Commit `ToDo.md` progress and `LearnedPatterns.md` via branch + PR
- [ ] Re-save `README.md` as UTF-8 (currently UTF-16 from PowerShell echo)
