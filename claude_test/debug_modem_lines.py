# Receive-only wiring probe: sample the converter's modem input lines and Windows comm error flags on the controller port. Never transmits.
"""Run only with the operator present (CommonClaude §5.1).

If a device wire landed on DB9 pin 1, 6, 8 or 9 instead of pin 2, the
matching input (CD, DSR, CTS, RI) may follow its voltage. A receive line
held at space shows up as a BREAK flag even when no bytes arrive.
"""

import argparse
import ctypes
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from laurell import SerialTransport, safety  # noqa: E402

sample_interval_s = 0.01
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="COM16")
    parser.add_argument("--baud", type=int, default=9600)
    parser.add_argument("--seconds", type=float, default=5.0)
    args = parser.parse_args()

    print(f"Transmit allowed by safety gate: {safety.is_transmit_allowed()}")
    states: Counter = Counter()
    error_bits = 0
    received = 0
    with SerialTransport(args.port, args.baud) as port:
        link = port._link
        print(f"Control lines after open: dtr={link.dtr} rts={link.rts}")
        read_comm_errors(link._port_handle)  # Clear stale flags from open.
        deadline = time.monotonic() + args.seconds
        while time.monotonic() < deadline:
            states[(link.cts, link.dsr, link.ri, link.cd)] += 1
            error_bits |= read_comm_errors(link._port_handle)
            received += len(port.read(port.in_waiting or 1))
            time.sleep(sample_interval_s)

    print(f"Samples over {args.seconds:.1f} s as (CTS, DSR, RI, CD):")
    for state, count in states.most_common():
        print(f"  {state}: {count}")
    flags = [name for bit, name in error_names.items() if error_bits & bit]
    print(f"Comm error flags: 0x{error_bits:X} {flags or '(none)'}")
    print(f"Bytes received: {received}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
