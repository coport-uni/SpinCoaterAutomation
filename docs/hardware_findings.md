# Hardware Findings

Facts about the device and the host link. Unconfirmed items are filled in
by bench measurement, not by inference.

## Device

Laurell WS-650MZ-23NPP/LITE, 650 Series Controller, board P/N 15000018
REV. C.

## Serial link (from `docs/development_spec.md` §4)

| Item | Value | Status |
|---|---|---|
| Transceiver | U18, SP3232EE, 16-pin TSSOP | Confirmed |
| Device TXD wire | Green, SP3232E pin 14 T1OUT | Confirmed |
| Device RXD wire | Yellow, SP3232E pin 13 R1IN | Confirmed |
| Ground wire | Probably black | Unconfirmed |
| Fourth wire | Pink or red, purpose unknown | Unconfirmed |
| Baud rate | Unknown | Unconfirmed |
| Frame format | Unknown | Unconfirmed |
| USB converter | NETmate KW-525, PL-2303, DB9 male | Confirmed |

## Host observations (2026-09-14)

Collected read-only from Windows 11 without opening the serial port.

| Item | Value | Source |
|---|---|---|
| Converter chip | Prolific PL2303GT, VID `067B`, PID `23A3` | Windows PnP |
| Converter driver | Prolific 5.2.12.0 (2026-07-07), service `plser`, problem code 0 | Windows PnP |
| Converter port | `COM16` | Windows PnP |
| Other ports | `COM3`, `COM4` are Bluetooth serial links, not the device | Windows PnP |
| Camera | Logitech HD Pro Webcam C920, VID `046D`, PID `08E5`, `usbvideo` | Windows PnP |
| Camera index | DirectShow index 2 (0 is a laptop camera, 1 a virtual camera) | `claude_test/debug_camera_frame.py` |
| Controller screen | 1920x1080 frame shows "Select Process" and "18 Processes Stored" | `claude_test/debug_camera_frame.py` |
| Current DB9 wiring | Not yet reported | Pending operator |

The spec's risk note about PL-2303 driver problems (§11) targets older
or counterfeit PL-2303 chips; this PL2303GT enumerates with the vendor
driver and no error.

## Control lines on open

pyserial 3.5 on Windows starts with DTR and RTS asserted and writes the
stored state into the port's DCB during `open()` (`serialwin32.py`).
`SerialTransport` therefore sets both lines low before opening and again
after. On the bench pyserial reported `dtr=False rts=False` after open;
this is the driver's software state, not a voltage measurement.

## Bench check (2026-09-14 17:29 KST, operator present)

Run with `claude_test/bench_transport_open.py --port COM16 --baud 9600
--seconds 3`, with C920 frames captured just before and after.

| Item | Result |
|---|---|
| Open `COM16`, 9600 8N1 | Opened, `is_open=True` |
| Control lines after open | `dtr=False rts=False` (software state) |
| Transmit attempt | Blocked with `TransmitBlockedError` (SAF-1); nothing sent |
| Close | `is_open=False` |
| Bytes received in 3 s | 0 |
| Controller screen | Unchanged: "Select Process", same LEDs, before and after |

Zero bytes is not explained by the unconfirmed baud rate alone: an active
line normally still yields bytes or framing errors at the wrong rate.
Possible causes, none confirmed:

- The controller does not transmit periodically on this screen or with
  this firmware (spec §11).
- The device TXD is not on DB9 pin 2, or signal ground is not on pin 5.
- The capture window of 3 s is shorter than the status period.

## Receive checks after rewiring (2026-09-15, operator present)

The operator changed the DB9 wiring before these runs. The new pin
assignment has not been recorded yet.

| Time (KST) | Run | Result |
|---|---|---|
| 08:53 | `bench_transport_open.py`, 9600 8N1, 10 s | 0 bytes; `dtr=False rts=False`; write blocked (SAF-1); screen unchanged |
| 08:57-09:00 | `debug_passive_scan.py`, 1200-115200 baud x 8N1/8E1/8O1/7E1, 5 s each | 0 bytes in all 32 combinations; screen unchanged before and after |

Before the scan, the checksum routines matched the published check values
for `123456789`, and the analyzer correctly identified synthetic Modbus
RTU (CRC-16/MODBUS), ASCII-line and STX/ETX+XOR8 captures. The null result
is therefore not an analysis failure.

Across about 170 s of listening the receive line produced no bytes at
all. Serial parameters cannot explain that: start bits on an active line
normally produce bytes at any baud rate or format, correct or not. The
problem lies before protocol decoding. Either no RS-232 signal reaches
DB9 pin 2 with ground on pin 5, or the controller does not transmit in
its current state.

Next checks that need no transmit:

1. With the controller on, measure DB9 pin 2 against pin 5 at the
   converter end. An idle RS-232 line reads about -5 V from this
   transceiver (`docs/serial_protocol_reference.md` §1.1); 0 V means the
   device TXD or ground does not reach those pins.
2. Capture for 60 s at any single setting while the operator presses
   non-motion keys (arrows, SELECT PROCESS, INFO). Line activity shows up
   regardless of baud rate.
3. Read the firmware version from the INFO screen through the C920
   (spec §11).

## Receive checks after second rewiring (2026-09-15, operator present)

The operator rewired the DB9 again before these runs. The pin assignment
has still not been recorded.

| Time (KST) | Run | Result |
|---|---|---|
| 09:09 | `bench_transport_open.py`, 9600 8N1, 10 s | 0 bytes; `dtr=False rts=False`; write blocked (SAF-1) |
| 09:09-09:12 | `debug_passive_scan.py`, 1200-115200 baud x 8N1/8E1/8O1/7E1, 5 s each | 0 bytes in all 32 combinations; checksum self-test passed |
| ~09:13 | `debug_modem_lines.py`, 10 s | CTS, DSR, RI, CD all `False` in 80 samples; no BREAK, FRAME, parity or overrun flags; 0 bytes |

C920 frames before and after show the same "Select Process" screen and
LEDs, so the controller did not react.

What the modem-line probe adds: no BREAK flag means the receive input is
not held at space, so it is at mark (idle RS-232, or an open input, which
the converter's receiver also reads as mark). No modem input changed, so
no device wire is visibly driving DB9 pin 1, 6, 8 or 9. From the PC side
a correctly wired but silent controller and an unconnected pin 2 look
identical. Only a voltage measurement or a known-good signal can
separate the two.

## Receive checks after third rewiring (2026-09-15, operator present)

The operator rewired the DB9 a third time and reported this assignment:
green (device TXD, SP3232E pin 14 T1OUT) to DB9 pin 2, yellow (device
RXD, pin 13 R1IN) to DB9 pin 3, black to DB9 pin 5. The pink/red wire is
not connected. A multimeter lead is visible next to the connector in the
C920 frames.

| Time (KST) | Run | Result |
|---|---|---|
| 09:21 | `debug_modem_lines.py`, 10 s | CTS, DSR, RI, CD all `False` in 81 samples; **BREAK flag set**; 0 bytes |
| 09:21-09:24 | `debug_passive_scan.py`, 32 combinations x 5 s | 0 bytes in all combinations; checksum self-test passed |

The controller screen was unchanged before and after.

The BREAK flag is new. Windows sets it when the receive input stays at
space (positive voltage) for longer than a character. An idle RS-232
transmitter sits at mark (negative), and an open input reads as mark, so
DB9 pin 2 is now held positive, which an idle TXD never does
(`docs/serial_protocol_reference.md` §1). With the green wire reported
on pin 2, the candidate causes, none confirmed, are:

- The transceiver output is really at space: the controller holds the
  TTL input T1IN (SP3232E pin 11) low, for example because its UART
  transmit is disabled. In that case this is the first wiring where the
  device TXD actually reaches the converter.
- Black is not signal ground, so pin 2 is measured against a floating
  reference.
- The green wire does not reach T1OUT at this end of the cable.

With pin 2 held at space no reply could be received, so transmit probing
in this wiring cannot show anything. Decision (operator, 2026-09-15):
fix the receive path first; no transmit until pin 2 idles at mark.

Measurements that separate the candidates, controller on:

| Probe (black lead / red lead) | Idle TXD expected | Meaning if different |
|---|---|---|
| DB9 pin 5 / DB9 pin 2 | about -5 V | about +5 V: transceiver output at space (first candidate); near 0 V: not connected |
| DB9 pin 5 / DB9 pin 3 | about -5 V (converter TXD idle) | near 0 V: pin 5 is not a common ground |
| Board GND / SP3232E pin 14 | about -5 V | Compare with the DB9 pin 2 reading to check the green wire |
| Board GND / SP3232E pin 11 | about +3.3 V (TTL idle high) | near 0 V: the controller holds its UART TX low |

### Operator voltage readings (2026-09-15, before 09:40 KST)

| Probe | Reported | Sign |
|---|---|---|
| DB9 pin 5 / DB9 pin 2 | 5.5 V | not stated |
| DB9 pin 5 / DB9 pin 3 | 5.5 V | not stated |

Whether the port was open during the reading was not recorded.

Receive-only cross-check at 09:40 KST, 3 runs x 5 s with
`debug_modem_lines.py`: **BREAK in every run**, CTS/DSR/RI/CD low,
0 bytes. The converter's receiver is sign-sensitive, so a persistent
BREAK means its input sees pin 2 at space (positive) the whole time.
The earlier BREAK was therefore not caused by a probe touching the line.
The previous wiring (09:13) showed no BREAK, so the current wiring
causes it.

The readings do not fit together cleanly:

- If both readings are +5.5 V, pin 2 matches the BREAK flag, but pin 3
  would mean the converter's own idle TXD is at space, which a PL2303
  converter does not do on its own. That points to a wrong reference:
  black on pin 5 may not be common signal ground.
- If both are -5.5 V (sign dropped or leads swapped), pin 3 is a normal
  idle TXD, but then pin 2 would be at mark and BREAK should not appear.
- +5.5 V is also the typical level of the SP3232E V+ charge-pump rail
  (pin 2), so a wire that lands on a rail instead of T1OUT would read
  the same.

Conclusion: pin 2 does not idle at mark, so the condition for the
transmit probe is still not met. Next checks, all without transmit:

1. Repeat both readings noting the sign, with black lead on DB9 pin 5,
   while `debug_modem_lines.py --seconds 60` holds the port open.
2. Power off everything (SAF-7) and check continuity: black to board
   GND (expect 0 ohm, reference §12 item 3), green to SP3232E pin 14,
   yellow to SP3232E pin 13.
3. Power off, move green off DB9 pin 2, power on, rerun
   `debug_modem_lines.py`. BREAK gone: the green wire drives pin 2
   positive. BREAK stays: look at the converter side.

### Transmit probe, CR / CRLF / ENQ (2026-09-15 09:47-09:48 KST)

Operator-directed, SAF-1 waived for this run only
(`claude_test/debug_tx_probe.py`). Wiring unchanged (green->2,
yellow->3, black->5). Operator present, chuck empty, lid closed. 24 sends:
CR `0d`, CRLF `0d 0a`, ENQ `05` at 1200-115200 baud, 8N1, each followed
by 1.5 s of listening. Log: `captures/tx_probe_20260915_094740/`.

| Baud | Baseline flags | After each probe |
|---|---|---|
| 1200, 2400 | BREAK | one `00` per sent byte, BREAK + FRAME |
| 4800 | BREAK | CR: one `00`, BREAK + FRAME; CRLF, ENQ: nothing, no flags |
| 9600-115200 | none | nothing, no flags |

The controller screen and LEDs were identical in C920 frames before and
after.

Reading of the result:

- **No reply from the controller at any baud rate.**
- The `00` bytes are not replies. Each arrived 1.0-4.4 ms after the
  transmit started, while one character at 1200 baud takes 8.3 ms, and
  there was exactly one `00` per byte sent. Our own transmission is
  coupling into the receive input while that input sits at space.
- BREAK disappeared from about 09:47:52 until the end of the run, then
  was back in a receive-only check at 09:49 KST (5 s, BREAK, 0 bytes).
  The receive input is unstable, not fixed.
- Consequently the 1200-4800 baud probes ran while replies could not be
  received, and the 9600-115200 probes ran with the line apparently at
  mark. Only the latter are a real negative result for CR / CRLF / ENQ.

The coupling from pin 3 to pin 2, the identical 5.5 V readings on both
pins, and the intermittent BREAK all point at the cable or grounding
rather than at the protocol. Before any further transmit, with power off:

1. Resistance DB9 pin 2 to pin 3 (a low value means the two lines touch).
2. Continuity black to board GND (reference §12 item 3).
3. Continuity green to SP3232E pin 14 and yellow to pin 13.

## Open questions

- Oscillator marking read as 19.6608M in a photo
  (`docs/serial_protocol_reference.md` §3.2); confirm on the board.
- Controller firmware version; firmware 47000022y and later stop
  periodic output while receiving remote commands (spec §11).
- The handover document `laurell_ws650_serial_protocol_brief.md` named in
  the spec is not in this repository.
