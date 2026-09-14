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

### pyserial asserts DTR and RTS on open by default
- **Problem**: A plain `serial.Serial(port)` raises DTR and RTS on a
  device whose reaction to those lines is unknown.
- **Cause**: `SerialBase` starts with `_dtr_state = _rts_state = True`
  and `serialwin32.py` writes that state into the DCB during `open()`.
- **Fix**: Build `serial.Serial()` unopened, set `dtr = rts = False`,
  then `open()`, and lower both again after opening.
- **Rule**: Never open a device port with the pyserial constructor
  shortcut; configure control lines before `open()`. (from ToDo#2)

### ruff format on the repo root touches Markdown
- **Problem**: `ruff format --check .` flags Python snippets inside
  `docs/*.md` and fails on the UTF-16 `README.md`.
- **Cause**: Ruff 0.16 also formats code blocks in Markdown files.
- **Fix**: Run the checks on the Python folders:
  `ruff check src tests claude_test`, `ruff format --check src tests
  claude_test`.
- **Rule**: Always pass explicit Python paths to ruff so reference
  documents are never rewritten. (from ToDo#2)

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

### Bench host has no Python on PATH
- **Problem**: `python` resolves to the Microsoft Store stub.
- **Cause**: Python is only installed through Miniconda.
- **Fix**: Use the `laurell` env by full path,
  `C:\Users\swoho\miniconda3\envs\laurell\python.exe`.
- **Rule**: Always call the `laurell` env interpreter explicitly on this
  host. (from ToDo#2)

### C920 is not camera index 0
- **Problem**: OpenCV index 0 opens the laptop camera, not the C920.
- **Cause**: DirectShow lists `LGE Camera`, then a virtual camera, then
  `HD Pro Webcam C920`.
- **Fix**: Resolve the index by name with `pygrabber` before
  `cv2.VideoCapture(index, cv2.CAP_DSHOW)`.
- **Rule**: Always select the bench camera by name, never by index.
  (from ToDo#2)

## §99. Uncategorized
