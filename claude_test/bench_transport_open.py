# M0 bench check: open the controller port receive-only through SerialTransport, listen briefly, close. Never transmits.
"""Run only with the operator present (CommonClaude §5.1).

The baud rate is not confirmed yet, so any bytes received are only a sign
of line activity, not decodable data.
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from laurell import SerialTransport, TransmitBlockedError, safety  # noqa: E402

preview_bytes = 64


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="COM16")
    parser.add_argument("--baud", type=int, default=9600)
    parser.add_argument("--seconds", type=float, default=3.0)
    args = parser.parse_args()

    print(f"Transmit allowed by safety gate: {safety.is_transmit_allowed()}")
    port = SerialTransport(args.port, args.baud)
    received = bytearray()
    with port:
        link = port._link
        print(f"Opened {args.port} at {args.baud} baud: is_open={port.is_open}")
        print(f"Control lines after open: dtr={link.dtr} rts={link.rts}")

        try:
            port.write(b"")
            print("UNEXPECTED: write was not blocked")
            return 1
        except TransmitBlockedError as error:
            print(f"Write blocked as expected: {error}")

        deadline = time.monotonic() + args.seconds
        while time.monotonic() < deadline:
            received += port.read(port.in_waiting or 1)

    print(f"Closed: is_open={port.is_open}")
    print(f"Received {len(received)} bytes in {args.seconds:.1f} s")
    if received:
        print(f"First bytes: {bytes(received[:preview_bytes]).hex(' ')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
