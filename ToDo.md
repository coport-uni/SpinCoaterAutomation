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

## Dev environment, camera check, and M0 scaffolding

### Background
User request (2026-09-14): read `docs/development_spec.md` and
`docs/serial_protocol_reference.md`, confirm the USB serial converter and
the Logitech camera are recognized, then (1) create a `laurell` conda
environment, (2) install hook tools, (3) grab one camera frame, and
(4) start milestone M0 through the normal ToDo / issue / branch flow.

### Findings (2026-09-14, read-only enumeration)
- Converter: Prolific PL2303GT, `COM16`, VID_067B PID_23A3, driver
  Prolific 5.2.12.0, problem code 0. The spec's PL-2303 driver risk
  (spec §11) does not apply to this chip.
- `COM3` and `COM4` are Bluetooth links, not the spin coater.
- Camera: Logitech HD Pro Webcam C920, VID_046D PID_08E5, `usbvideo`,
  problem code 0. The host also exposes LGE laptop cameras and a
  Mirametrix virtual camera, so the C920 must be selected by name.
- `COM16` has not been opened; some drivers assert DTR/RTS on open
  (reference §10), and no transport with the SAF-1 guard exists yet.
- No Python on `PATH`; Miniconda exists at `C:\Users\swoho\miniconda3`.

### Tasks: environment and camera (approved by user 2026-09-14)
- [x] Enumerate serial and camera devices without opening them
- [x] Create conda env `laurell` (Python 3.12, conda-forge) with
  pyserial, opencv-python, pygrabber, numpy, matplotlib, pytest,
  pytest-cov, ruff, mypy
- [x] Install hook dependency `jq` via winget (already installed; VS Code
  restart needed to pick up `PATH`, see LP §5)
- [x] Put `ruff` on `PATH` for the lint hook (env `ruff` is not on `PATH`;
  proposal: `winget install astral-sh.ruff`, awaiting confirmation)
- [x] Grab one C920 frame with `claude_test/debug_camera_frame.py`
- [x] Record the script in `claude_test/README.md`

### Tasks: M0 scaffolding (spec §7 M0, §12 steps 1-4; awaiting confirmation)
- [x] Create GitHub issue for this task (#3)
- [x] Cut `feature/m0-scaffolding` from `main`
- [x] Create spec §6 layout in this repository: `src/laurell/`, `tests/`,
  `tests/fixtures/`, `analysis/notebooks/`, `analysis/scripts/`,
  `captures/.gitkeep`
- [x] Write `SAFETY.md` with spec §3 verbatim
- [x] Write `docs/hardware_findings.md` from spec §4 plus the findings above
- [x] Extend `pyproject.toml`: project metadata, dependencies, Ruff
  (80 columns), mypy, pytest `hardware` marker excluded by default
- [x] Define exception hierarchy (`LaurellError`, `TransportError`,
  `TransmitBlockedError`, ...) per spec §7 M5 table
- [x] Implement receive-only `SerialTransport` in
  `src/laurell/transport.py` (DTR/RTS low on open, `write` raises
  `TransmitBlockedError` unless `LAURELL_TX_ENABLED=1`, context manager,
  SAFETY header comment)
- [x] Add `tests/test_transport.py` with mocked pyserial
- [x] Verify: `ruff check`, `ruff format --check`, `mypy src`, `pytest`
- [x] Bench check with operator present: open `COM16` receive-only via
  `SerialTransport`, confirm no TX and clean close (CommonClaude §5.1)
- [x] Commit per feature, push, open PR with Testing output, update issue
  (PR #4)

## Passive protocol scan after rewiring

### Background
User request (2026-09-15): the operator changed the DB9 wiring; retry
reception and try every known communication protocol.

### Decisions (2026-09-15)
- Interpreted as receive-only. SAF-1 forbids any transmit before M3, so
  request/response probing (CR, CRLF, ENQ, Modbus queries; spec M4) is
  not attempted.
- The scan is an exploratory script in `claude_test/`, not the M1
  `baudscan.py`, because M0 (PR #4) is not merged yet (WR-1). The branch
  is stacked on `feature/m0-scaffolding` so it can use `SerialTransport`.

### Tasks
- [x] Re-run receive-only bench check after rewiring (9600 8N1, 10 s,
  C920 frames before and after): 0 bytes, controller screen unchanged
- [x] Create GitHub issue for this task (#5)
- [x] Cut `feature/passive-protocol-scan` from `feature/m0-scaffolding`
- [ ] Write `claude_test/debug_passive_scan.py`: 8 baud rates (1200 to
  115200) x 4 formats (8N1, 8E1, 8O1, 7E1), 5 s each, JSONL per spec M1,
  shape checks (ASCII line, STX/ETX, Modbus RTU CRC, fixed-length binary,
  repeated sequences), checksum search per reference §8
- [x] Self-test checksum implementations against published check values
- [x] Run `ruff check` and `ruff format --check` on the script
- [x] Validate the analyzer on synthetic Modbus RTU, ASCII-line and
  STX/ETX+XOR8 captures; add `--reanalyze` (found and fixed two bugs,
  see LP §2)
- [x] Run the scan with the operator present, no transmit (0 bytes in
  all 32 combinations)
- [x] Record results in `docs/hardware_findings.md` and
  `claude_test/README.md`
- [ ] Commit, push, open PR, update issue
- [ ] Record the new DB9 pin assignment from the operator
- [ ] Operator: measure DB9 pin 2 vs pin 5 with the controller on
- [ ] Capture 60 s while the operator presses non-motion keys
- [ ] Read firmware version from the INFO screen via the C920
