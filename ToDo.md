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
- [x] Commit, push, open PR, update issue (PR #6, stacked on #4)
- [ ] Record the new DB9 pin assignment from the operator
- [ ] Operator: measure DB9 pin 2 vs pin 5 with the controller on
- [ ] Capture 60 s while the operator presses non-motion keys
- [ ] Read firmware version from the INFO screen via the C920

### Retry after second rewiring (user request 2026-09-15)
- [x] Confirm `COM16` and C920 still enumerate (both OK)
- [x] Receive-only bench check, 9600 8N1, 10 s (0 bytes, 09:09 KST)
- [x] Passive scan, 32 combinations x 5 s (0 bytes, 09:09-09:12 KST)
- [x] Add `claude_test/debug_modem_lines.py` and sample CTS/DSR/RI/CD and
  comm error flags (all low, no flags, 0 bytes)
- [x] Record results in `docs/hardware_findings.md` and
  `claude_test/README.md`
- [x] Run `ruff check` and `ruff format --check` on the new script
- [x] Commit, push to PR #6, comment on issue #5

### Retry after third rewiring (user request 2026-09-15)
- [x] Confirm `COM16` and C920 still enumerate (both OK)
- [x] Modem-line probe, 10 s (all low, BREAK flag set, 0 bytes, 09:21 KST)
- [x] Passive scan, 32 combinations x 5 s (0 bytes, 09:21-09:24 KST)
- [x] Record results in `docs/hardware_findings.md`
- [x] User asked to also transmit probes and watch for replies or error
  codes; this conflicts with SAF-1 (no transmit before M3). Decision
  (user, 2026-09-15): fix the receive path first, no transmit yet. For a
  later send test the user picked all 8 baud rates at 8N1 and confirmed
  the bench is ready (chuck empty, lid closed, STOP in reach)
- [x] Record the DB9 pin assignment (green TXD->2, yellow RXD->3,
  black->5, pink/red unconnected)
- [x] Operator: measure DB9 pin 2 and pin 3 against pin 5 (both 5.5 V,
  sign not stated)
- [x] Receive-only cross-check 09:40 KST, 3 x 5 s: BREAK every run, so
  pin 2 is at space; transmit condition still not met
- [ ] Operator: repeat readings with sign while the port is held open
- [ ] Operator, power off: continuity black->board GND, green->SP3232E
  pin 14, yellow->pin 13
- [ ] Operator: lift green off DB9 pin 2 and rerun the modem-line probe
- [ ] SP3232E pin 14 and pin 11 against board GND

### Transmit probe (user request 2026-09-15, overrides "fix RX first")
- [x] Write `claude_test/debug_tx_probe.py`: allowlist CR, CRLF, ENQ;
  8N1; SAF-1 waived in-process only; needs `LAURELL_TX_ENABLED=1` and
  `--send`; records replies and comm error flags
- [x] Ruff checks on the script
- [x] Run it: first attempt blocked by the auto-mode classifier; user
  then directed all of CR/CRLF/ENQ. Ran 09:47 KST, 24 sends: no
  controller reply, screen unchanged; `00`+FRAME per sent byte at
  1200-4800 is local TX coupling; BREAK returned by 09:49
- [x] Resolve conflict: 09:38 "no BREAK" note in `claude_test/README.md`
  kept with a correction citing the 09:40 and 09:49 BREAK runs
- [ ] Operator, power off: resistance DB9 pin 2 to pin 3, continuity
  black->board GND, green->SP3232E 14, yellow->13
- [ ] No further transmit until the receive input idles at mark

### Probe after TX/RX swap (user request 2026-09-15)
- [x] Line check, CR/CRLF/ENQ x 8 baud rates, line check, C920 frames
  (09:58-09:59 KST): no reply, echo gone, BREAK persists
- [x] Correct the earlier "BREAK vanished mid-run" reading: the pattern
  repeated exactly, so it is a sampling artefact of the probe
- [ ] Operator: report the swapped pin assignment and which pins read
  -8 V (black lead on which pin)

### Wire resistance analysis (user request 2026-09-15)
- [x] Record operator's wire-to-wire resistance table and interpret it:
  G and B behave as one node (R-Y = R-G + G-Y), R and Y about 5 kΩ to
  it, so R and Y are the likely signal pair
- [ ] Operator: confirm whether "1" on G-B means short or over-range
- [ ] Operator: G-B again with both cable ends unplugged
- [ ] Operator: controller on, converter unplugged, R and Y against B
  (about -5.4 V = device TXD, about 0 V = device RXD)
- [ ] Rewire with power off: TXD->2, RXD->3, B->5, G unconnected; then
  repeat the receive-only scan
- [x] Commit, push to PR #6, comment on issue #5
