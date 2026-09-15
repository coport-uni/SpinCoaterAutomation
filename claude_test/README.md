# claude_test

Debug scripts, one-off experiments, and diagnostic code (CommonClaude §3).
Production tests belong in `tests/`.

| File | Purpose | What was learned |
|------|---------|------------------|
| `debug_camera_frame.py` | Grab one frame from the Logitech C920 selected by DirectShow name (`--out <png>`). | DirectShow order on this host is `[0] LGE Camera`, `[1] Mirametrix Virtual Camera`, `[2] HD Pro Webcam C920`, so index 0 is the wrong camera. 1920x1080 works; 31 reads take about 7 s including auto-exposure warm-up. The frame shows the 650 controller LCD legibly (2026-09-14). |
| `bench_transport_open.py` | M0 bench check: open `COM16` receive-only through `SerialTransport`, confirm DTR/RTS low and write blocked, listen a few seconds, close. Operator must be present. | Run 2026-09-14 17:29 KST with operator present: opened at 9600 8N1, `dtr=False rts=False`, write blocked by SAF-1, closed cleanly, controller screen unchanged in before/after C920 frames. Received 0 bytes in 3 s, so there was no line activity at all; check DB9 wiring and whether the controller streams periodically before M1. |
| `debug_passive_scan.py` | Receive-only scan over 8 baud rates x 4 formats (8N1, 8E1, 8O1, 7E1); saves JSONL per spec M1 under `captures/`, checks ASCII line, STX/ETX, Modbus RTU CRC, fixed-length and repeated-sequence structure, and searches the reference §8 checksums. `--self-test-only` verifies the checksums against `123456789` check values; `--reanalyze <session_dir>` re-runs the analysis on saved JSONL without opening the port. Operator must be present for a live scan. | Synthetic check first found two analyzer bugs (CR/LF strip ate `0x0D` CRC bytes; a lone `0x02` faked an STX frame), both fixed. Live run 2026-09-15 08:57-09:00 KST after rewiring: 0 bytes in all 32 combinations, controller screen unchanged. No signal reaches the RX line, so the cause is wiring or a silent controller, not serial parameters. |
