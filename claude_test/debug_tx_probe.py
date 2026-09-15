# Operator-directed transmit probe: send CR, CRLF, ENQ at each baud rate (8N1) and record replies and comm error flags. Waives SAF-1 in this process only. Exploratory (spec M4 steps 1-3).
"""Run only with the operator present, chuck empty, lid closed, STOP in reach.

SAFETY.md SAF-1 forbids transmit before M3. The operator explicitly
directed this probe on 2026-09-15 (issue #5). The waiver lives only in
this process: ``safety.transmit_milestone_reached`` is flipped in memory,
never in ``src/``. SAF-2 still applies (``LAURELL_TX_ENABLED=1`` must be
set by the caller), SAF-3 still applies (dry run unless ``--send``), and
SAF-4 is kept by sending only the fixed allowlist below.

A reply sent at a different baud rate still shows up as garbled bytes or
FRAME errors, so the error flags are recorded after every probe.
"""

import argparse
import ctypes
import json
import sys
import time
from datetime import datetime
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "src"))

from laurell import SerialTransport, safety  # noqa: E402

# SAF-4: the only frames this script can send. None can start the motor.
probe_allowlist = {
    "CR": b"\r",
    "CRLF": b"\r\n",
    "ENQ": b"\x05",
}
baud_rates = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]
baseline_s = 0.5
listen_s = 1.5
poll_s = 0.01
error_names = {
    0x10: "BREAK",
    0x08: "FRAME",
    0x04: "RXPARITY",
    0x02: "OVERRUN",
    0x01: "RXOVER",
}


def read_comm_errors(handle: int) -> int:
    errors = ctypes.c_ulong()
    ctypes.windll.kernel32.ClearCommError(handle, ctypes.byref(errors), None)
    return errors.value


def flag_names(bits: int) -> str:
    return ",".join(n for b, n in error_names.items() if bits & b) or "-"


def to_ascii(data: bytes) -> str:
    return "".join(chr(b) if 0x20 <= b <= 0x7E else "." for b in data)


def listen(port: SerialTransport, seconds: float, log, label: str):
    handle = port._link._port_handle
    received = bytearray()
    bits = 0
    previous = time.perf_counter()
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        bits |= read_comm_errors(handle)
        data = port.read(port.in_waiting or 1)
        if data:
            now = time.perf_counter()
            log(
                {
                    "ts": round(time.time(), 6),
                    "dir": "rx",
                    "hex": data.hex(" "),
                    "ascii": to_ascii(data),
                    "gap_us": int((now - previous) * 1e6),
                    "after": label,
                }
            )
            previous = now
            received += data
        time.sleep(poll_s)
    bits |= read_comm_errors(handle)
    return bytes(received), bits


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="COM16")
    parser.add_argument("--bauds", type=int, nargs="+", default=baud_rates)
    parser.add_argument(
        "--probes",
        nargs="+",
        default=list(probe_allowlist),
        choices=list(probe_allowlist),
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="Actually transmit. Without it only the plan is printed.",
    )
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    plan = [(b, p) for b in args.bauds for p in args.probes]
    print(f"Plan: {len(plan)} sends on {args.port}, 8N1")
    for baud in args.bauds:
        frames = ", ".join(
            f"{p}={probe_allowlist[p].hex(' ')}" for p in args.probes
        )
        print(f"  {baud:>6}: {frames}")
    if not args.send:
        print("Dry run: nothing opened, nothing sent. Pass --send to run.")
        return 0

    print("!! SAF-1 waived in this process by operator direction (issue #5)")
    safety.transmit_milestone_reached = True
    if not safety.is_transmit_allowed():
        print(f"Blocked: set {safety.tx_enabled_variable}=1 (SAF-2).")
        return 1

    stamp = datetime.now().astimezone()
    out_dir = repo_root / "captures" / f"tx_probe_{stamp:%Y%m%d_%H%M%S}"
    out_dir.mkdir(parents=True, exist_ok=True)
    events = (out_dir / "events.jsonl").open("w", encoding="utf-8")

    def log(event: dict) -> None:
        events.write(json.dumps(event) + "\n")
        events.flush()

    rows = []
    print(f"{'baud':>6} {'probe':<9} {'rx bytes':>8}  flags        reply")
    try:
        for baud in args.bauds:
            with SerialTransport(args.port, baud) as port:
                read_comm_errors(port._link._port_handle)
                port._link.reset_input_buffer()
                data, bits = listen(port, baseline_s, log, "baseline")
                rows.append((baud, "baseline", data, bits))
                print(
                    f"{baud:>6} {'baseline':<9} {len(data):>8}  "
                    f"{flag_names(bits):<12} {data[:24].hex(' ')}"
                )
                for probe in args.probes:
                    frame = probe_allowlist[probe]
                    read_comm_errors(port._link._port_handle)
                    written = port.write(frame, dry_run=False)
                    port._link.flush()
                    log(
                        {
                            "ts": round(time.time(), 6),
                            "dir": "tx",
                            "hex": frame.hex(" "),
                            "ascii": to_ascii(frame),
                            "gap_us": None,
                            "baud": baud,
                            "probe": probe,
                            "written": written,
                        }
                    )
                    data, bits = listen(port, listen_s, log, probe)
                    rows.append((baud, probe, data, bits))
                    print(
                        f"{baud:>6} {probe:<9} {len(data):>8}  "
                        f"{flag_names(bits):<12} {data[:24].hex(' ')}"
                        f"  {to_ascii(data[:24])}"
                    )
    finally:
        events.close()
        safety.transmit_milestone_reached = False

    session = {
        "port": args.port,
        "format": "8N1",
        "bauds": args.bauds,
        "probes": {p: probe_allowlist[p].hex(" ") for p in args.probes},
        "started_at": stamp.isoformat(),
        "ended_at": datetime.now().astimezone().isoformat(),
        "operator_notes": args.notes,
        "results": [
            {
                "baud": b,
                "probe": p,
                "rx_hex": d.hex(" "),
                "flags": flag_names(f),
            }
            for b, p, d, f in rows
        ],
    }
    (out_dir / "session.json").write_text(
        json.dumps(session, indent=2), encoding="utf-8"
    )
    replies = [r for r in rows if r[1] != "baseline" and r[2]]
    print(f"\nProbes with reply bytes: {len(replies)} / {len(plan)}")
    print(f"Saved {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
