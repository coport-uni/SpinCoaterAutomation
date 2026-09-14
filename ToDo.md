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

### Tasks
- [x] Initialize git repository (`main`)
- [x] Add submodule `external/CommonClaude`
- [x] Install hook dependency `jq` via winget
- [x] Write root `CLAUDE.md` with import and project overrides
- [ ] Write root `.claude/settings.json` wiring submodule hooks
- [x] Add `.gitignore` (CommonClaude §13.1), `pyproject.toml` (Ruff, §6)
- [x] Add `claude_test/README.md` index (§3)
- [ ] Verify each hook with sample tool payloads on Windows Git Bash
- [ ] Create GitHub repository and issue (needs user decision on remote)
- [ ] Initial commit after verification
