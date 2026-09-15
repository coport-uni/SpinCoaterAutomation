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

## Open questions

- Oscillator marking read as 19.6608M in a photo
  (`docs/serial_protocol_reference.md` §3.2); confirm on the board.
- Controller firmware version; firmware 47000022y and later stop
  periodic output while receiving remote commands (spec §11).
- The handover document `laurell_ws650_serial_protocol_brief.md` named in
  the spec is not in this repository.
