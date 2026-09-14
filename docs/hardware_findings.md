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

## Open questions

- Oscillator marking read as 19.6608M in a photo
  (`docs/serial_protocol_reference.md` §3.2); confirm on the board.
- Controller firmware version; firmware 47000022y and later stop
  periodic output while receiving remote commands (spec §11).
- The handover document `laurell_ws650_serial_protocol_brief.md` named in
  the spec is not in this repository.
