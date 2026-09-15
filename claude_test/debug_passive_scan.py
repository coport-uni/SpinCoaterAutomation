# Passive protocol scan: listen on the controller port at every standard baud rate and frame format, then test the bytes against known serial protocol shapes. Receive-only; never transmits. Exploratory, to be replaced by M1 baudscan.py.
"""Run only with the operator present (CommonClaude §5.1).

For each baud rate and frame format the port is opened through
SerialTransport (DTR/RTS low, transmit gate closed), bytes are captured
with timestamps, and the capture is checked for the protocol families in
docs/serial_protocol_reference.md §6 plus the checksums in §8.

Timing is per read chunk, not per byte: Windows and the PL2303 driver
deliver bytes in batches, so gap_us is the gap between chunks.
"""

import argparse
import json
import re
import sys
import time
import zlib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "src"))

import serial  # noqa: E402

from laurell import SerialTransport, safety  # noqa: E402

baud_rates = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]
frame_formats = {
    "8N1": (serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE),
    "8E1": (serial.EIGHTBITS, serial.PARITY_EVEN, serial.STOPBITS_ONE),
    "8O1": (serial.EIGHTBITS, serial.PARITY_ODD, serial.STOPBITS_ONE),
    "7E1": (serial.SEVENBITS, serial.PARITY_EVEN, serial.STOPBITS_ONE),
}
read_timeout_s = 0.01
# Windows cannot resolve gaps much below its scheduler tick.
min_idle_s = 0.005
modbus_idle_chars = 3.5
min_frames = 3
match_ratio = 0.9
stx, etx = 0x02, 0x03
printable_extra = {0x09, 0x0A, 0x0D}


# ----- Checksums (reference §8) --------------------------------------------


def reflect(value: int, width: int) -> int:
    result = 0
    for _ in range(width):
        result = (result << 1) | (value & 1)
        value >>= 1
    return result


def make_crc(width, poly, init, refin, refout, xorout):
    top_bit = 1 << (width - 1)
    mask = (1 << width) - 1

    def crc(data: bytes) -> int:
        value = init
        for byte in data:
            if refin:
                byte = reflect(byte, 8)
            value ^= byte << (width - 8)
            for _ in range(8):
                if value & top_bit:
                    value = ((value << 1) ^ poly) & mask
                else:
                    value = (value << 1) & mask
        if refout:
            value = reflect(value, width)
        return value ^ xorout

    return crc


def xor8(data: bytes) -> int:
    value = 0
    for byte in data:
        value ^= byte
    return value


def sum8(data: bytes) -> int:
    return sum(data) & 0xFF


def twos_complement_sum8(data: bytes) -> int:
    # Identical to the binary LRC of reference §8.
    return (-sum(data)) & 0xFF


# name -> (width in bytes, function)
checksums = {
    "xor8": (1, xor8),
    "sum8": (1, sum8),
    "twos_sum8_lrc": (1, twos_complement_sum8),
    "crc8": (1, make_crc(8, 0x07, 0x00, False, False, 0x00)),
    "crc8_maxim": (1, make_crc(8, 0x31, 0x00, True, True, 0x00)),
    "crc16_modbus": (2, make_crc(16, 0x8005, 0xFFFF, True, True, 0x0000)),
    "crc16_ccitt_false": (
        2,
        make_crc(16, 0x1021, 0xFFFF, False, False, 0x0000),
    ),
    "crc16_xmodem": (2, make_crc(16, 0x1021, 0x0000, False, False, 0x0000)),
    "crc16_kermit": (2, make_crc(16, 0x1021, 0x0000, True, True, 0x0000)),
    "crc32": (4, lambda data: zlib.crc32(data) & 0xFFFFFFFF),
}

# Published "check" values for the ASCII input 123456789 (CRC RevEng
# catalogue); sums computed by hand: sum = 0x1DD.
check_input = b"123456789"
check_values = {
    "xor8": 0x31,
    "sum8": 0xDD,
    "twos_sum8_lrc": 0x23,
    "crc8": 0xF4,
    "crc8_maxim": 0xA1,
    "crc16_modbus": 0x4B37,
    "crc16_ccitt_false": 0x29B1,
    "crc16_xmodem": 0x31C3,
    "crc16_kermit": 0x2189,
    "crc32": 0xCBF43926,
}


def self_test() -> bool:
    ok = True
    for name, (_, function) in checksums.items():
        got = function(check_input)
        passed = got == check_values[name]
        ok &= passed
        print(
            f"  {name:<18} got 0x{got:X} expected 0x{check_values[name]:X} {'ok' if passed else 'FAIL'}"
        )
    return ok


def decode_trailer(trailer: bytes, encoding: str) -> int | None:
    if encoding == "raw_be":
        return int.from_bytes(trailer, "big")
    if encoding == "raw_le":
        return int.from_bytes(trailer, "little")
    text = trailer.decode("ascii", errors="replace")
    if re.fullmatch(r"[0-9A-Fa-f]+", text):
        return int(text, 16)
    return None


def find_checksums(frames: list[bytes]) -> list[dict]:
    # No CR/LF stripping here: a binary checksum byte can be 0x0A or 0x0D.
    # Line frames already arrive without their terminators.
    frames = [f for f in frames if len(f) >= 3]
    if len(frames) < min_frames:
        return []
    hits = []
    for name, (width, function) in checksums.items():
        encodings = ["raw_be", "ascii_hex"] + (["raw_le"] if width > 1 else [])
        for encoding in encodings:
            size = width * 2 if encoding == "ascii_hex" else width
            for layout in ("all", "skip_first", "stx_etx_body"):
                usable = matched = 0
                for frame in frames:
                    if len(frame) <= size:
                        continue
                    head, trailer = frame[:-size], frame[-size:]
                    if layout == "all":
                        body = head
                    elif layout == "skip_first":
                        body = head[1:]
                    else:
                        if not (
                            head[:1] == bytes([stx])
                            and head[-1:] == bytes([etx])
                        ):
                            continue
                        body = head[1:-1]
                    expected = decode_trailer(trailer, encoding)
                    if not body or expected is None:
                        continue
                    usable += 1
                    matched += function(body) == expected
                if usable >= min_frames and matched / usable >= match_ratio:
                    hits.append(
                        {
                            "algorithm": name,
                            "encoding": encoding,
                            "layout": layout,
                            "matched": matched,
                            "usable": usable,
                            "distinct_frames": len(set(frames)),
                        }
                    )
    return hits


# ----- Capture --------------------------------------------------------------


def to_ascii(data: bytes) -> str:
    return "".join(chr(b) if 0x20 <= b <= 0x7E else "." for b in data)


def capture(
    port_name: str, baud: int, fmt: str, seconds: float
) -> list[tuple[float, float, bytes]]:
    """Return (unix_ts, perf_counter, chunk) for every non-empty read."""
    bytesize, parity, stopbits = frame_formats[fmt]
    chunks = []
    transport = SerialTransport(
        port_name,
        baud,
        bytesize=bytesize,
        parity=parity,
        stopbits=stopbits,
        timeout=read_timeout_s,
    )
    with transport:
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            waiting = transport.in_waiting
            data = transport.read(waiting or 1)
            if data:
                chunks.append((time.time(), time.perf_counter(), data))
    return chunks


def write_jsonl(path: Path, chunks) -> None:
    previous = None
    with path.open("w", encoding="utf-8") as handle:
        for unix_ts, mono, data in chunks:
            gap_us = None if previous is None else int((mono - previous) * 1e6)
            previous = mono
            event = {
                "ts": round(unix_ts, 6),
                "dir": "rx",
                "hex": data.hex(" "),
                "ascii": to_ascii(data),
                "gap_us": gap_us,
            }
            handle.write(json.dumps(event) + "\n")


# ----- Analysis (reference §6, §9) -------------------------------------------


def split_by_idle(chunks, idle_s: float) -> list[bytes]:
    frames, current, previous = [], bytearray(), None
    for _, mono, data in chunks:
        if previous is not None and mono - previous > idle_s and current:
            frames.append(bytes(current))
            current = bytearray()
        current += data
        previous = mono
    if current:
        frames.append(bytes(current))
    return frames


def analyze(chunks, baud: int, fmt: str) -> dict:
    data = b"".join(chunk for _, _, chunk in chunks)
    total = len(data)
    result = {
        "baud": baud,
        "format": fmt,
        "bytes": total,
        "chunks": len(chunks),
    }
    if total == 0:
        result.update(score=0.0, shapes=[], checksum_hits=[])
        return result

    bytesize, parity, stopbits = frame_formats[fmt]
    bits_per_char = 1 + bytesize + (parity != serial.PARITY_NONE) + stopbits
    char_s = bits_per_char / baud
    idle_s = max(modbus_idle_chars * char_s, min_idle_s)

    printable = (
        sum(1 for b in data if 0x20 <= b <= 0x7E or b in printable_extra)
        / total
    )
    null_ff = sum(1 for b in data if b in (0x00, 0xFF)) / total
    grams = Counter(data[i : i + 4] for i in range(total - 3))
    top_gram, top_count = grams.most_common(1)[0] if grams else (b"", 0)
    repeat = min(1.0, (top_count - 1) * 4 / total) if top_count > 1 else 0.0

    idle_frames = split_by_idle(chunks, idle_s)
    line_frames = [f for f in re.split(rb"\r\n|\r|\n", data) if f]
    stx_frames = [bytes([stx]) + part for part in data.split(bytes([stx]))[1:]]

    newline_count = data.count(b"\r") + data.count(b"\n")
    modbus_candidates = [f for f in idle_frames if len(f) >= 4]
    modbus_crc = checksums["crc16_modbus"][1]
    modbus_ok = sum(
        1
        for f in modbus_candidates
        if modbus_crc(f[:-2]) == int.from_bytes(f[-2:], "little")
    )
    modbus_ratio = (
        modbus_ok / len(modbus_candidates) if modbus_candidates else 0.0
    )
    lengths = Counter(len(f) for f in idle_frames)
    fixed_share = (
        lengths.most_common(1)[0][1] / len(idle_frames)
        if len(idle_frames) >= min_frames
        else 0.0
    )
    stx_with_etx = sum(1 for f in stx_frames if etx in f)

    shapes = []
    if printable >= match_ratio and newline_count:
        shapes.append(f"ascii_line ({len(line_frames)} lines)")
    # A lone 0x02 inside binary data would otherwise look like one frame.
    if (
        len(stx_frames) >= min_frames
        and stx_with_etx / len(stx_frames) >= match_ratio
    ):
        shapes.append(f"stx_etx ({len(stx_frames)} frames)")
    if len(modbus_candidates) >= min_frames and modbus_ratio >= match_ratio:
        shapes.append(
            f"modbus_rtu ({modbus_ok}/{len(modbus_candidates)} CRC ok)"
        )
    if fixed_share >= match_ratio:
        shapes.append(f"fixed_length ({lengths.most_common(1)[0][0]} bytes)")

    checksum_hits = []
    for source, frames in (
        ("idle", idle_frames),
        ("line", line_frames),
        ("stx", stx_frames),
    ):
        for hit in find_checksums(frames):
            checksum_hits.append({"frames": source, **hit})

    structure = max(modbus_ratio, fixed_share, 1.0 if shapes else 0.0)
    score = 3 * printable + 3 * repeat + structure - null_ff
    result.update(
        printable_ratio=round(printable, 3),
        null_ff_ratio=round(null_ff, 3),
        top_4gram=top_gram.hex(" "),
        top_4gram_count=top_count,
        repeat_score=round(repeat, 3),
        idle_threshold_ms=round(idle_s * 1e3, 2),
        idle_frames=len(idle_frames),
        newline_count=newline_count,
        stx_frames=len(stx_frames),
        modbus_crc_ratio=round(modbus_ratio, 3),
        fixed_length_share=round(fixed_share, 3),
        shapes=shapes,
        checksum_hits=checksum_hits,
        score=round(score, 3),
        preview_hex=data[:48].hex(" "),
        preview_ascii=to_ascii(data[:48]),
    )
    return result


# ----- Re-analysis of saved sessions -----------------------------------------


def load_jsonl(path: Path) -> list[tuple[float, float, bytes]]:
    """Rebuild capture chunks from a JSONL file written by write_jsonl."""
    chunks, mono = [], 0.0
    for line in path.read_text(encoding="utf-8").splitlines():
        event = json.loads(line)
        if event["dir"] != "rx":
            continue
        if event["gap_us"] is not None:
            mono += event["gap_us"] / 1e6
        chunks.append((event["ts"], mono, bytes.fromhex(event["hex"])))
    return chunks


def reanalyze(session_dir: Path) -> int:
    """Re-run the analysis on a saved session without opening the port."""
    format_order = list(frame_formats)
    captures = []
    for path in session_dir.glob("*_*.jsonl"):
        baud_text, fmt = path.stem.split("_", 1)
        if baud_text.isdigit() and fmt in frame_formats:
            captures.append((int(baud_text), fmt, path))
    if not captures:
        print(f"No capture files in {session_dir}")
        return 1
    captures.sort(key=lambda c: (c[0], format_order.index(c[1])))

    print(f"Re-analyzing {len(captures)} captures in {session_dir}")
    results = []
    for baud, fmt, path in captures:
        result = analyze(load_jsonl(path), baud, fmt)
        results.append(result)
        print(
            f"{baud:>6} {fmt:<4} {result['bytes']:>6} "
            f"chunks={result['chunks']:<5} score={result['score']:<6} "
            f"shapes={', '.join(result['shapes']) or '-'}"
        )
        for hit in result["checksum_hits"]:
            print(f"         checksum: {hit}")
    (session_dir / "summary_reanalyzed.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )
    total_bytes = sum(r["bytes"] for r in results)
    print(f"Total bytes over all combinations: {total_bytes}")
    return 0


# ----- Main -----------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="COM16")
    parser.add_argument("--seconds", type=float, default=5.0)
    parser.add_argument("--bauds", type=int, nargs="+", default=baud_rates)
    parser.add_argument(
        "--formats",
        nargs="+",
        default=list(frame_formats),
        choices=list(frame_formats),
    )
    parser.add_argument("--out-dir", type=Path, default=repo_root / "captures")
    parser.add_argument("--notes", default="")
    parser.add_argument("--self-test-only", action="store_true")
    parser.add_argument(
        "--reanalyze",
        type=Path,
        help="Analyze a saved passive_scan_* directory; the port is not used.",
    )
    args = parser.parse_args()

    print("Checksum self-test (input '123456789'):")
    if not self_test():
        print("Self-test failed; not scanning.")
        return 1
    if args.self_test_only:
        return 0
    if args.reanalyze:
        return reanalyze(args.reanalyze)

    if safety.is_transmit_allowed():
        print("Transmit gate is open; this passive scan refuses to run.")
        return 1
    print("Transmit allowed by safety gate: False (receive-only)")

    started = datetime.now(timezone.utc).astimezone()
    session_dir = args.out_dir / f"passive_scan_{started:%Y%m%d_%H%M%S}"
    session_dir.mkdir(parents=True, exist_ok=True)
    combos = [(b, f) for b in args.bauds for f in args.formats]
    print(
        f"Scanning {len(combos)} combinations x {args.seconds:.1f} s on {args.port} -> {session_dir}"
    )

    results = []
    header = f"{'baud':>6} {'fmt':<4} {'bytes':>6} {'print':>5} {'repeat':>6} {'null/FF':>7} {'score':>6}  shapes"
    print(header)
    for baud, fmt in combos:
        chunks = capture(args.port, baud, fmt, args.seconds)
        write_jsonl(session_dir / f"{baud}_{fmt}.jsonl", chunks)
        result = analyze(chunks, baud, fmt)
        results.append(result)
        print(
            f"{baud:>6} {fmt:<4} {result['bytes']:>6} "
            f"{result.get('printable_ratio', 0):>5.2f} {result.get('repeat_score', 0):>6.2f} "
            f"{result.get('null_ff_ratio', 0):>7.2f} {result['score']:>6.2f}  "
            f"{', '.join(result['shapes']) or '-'}"
        )

    ended = datetime.now(timezone.utc).astimezone()
    session = {
        "port": args.port,
        "baudrate": args.bauds,
        "formats": args.formats,
        "seconds_per_combo": args.seconds,
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "operator_notes": args.notes,
        "firmware": None,
        "serial_number": None,
        "model": None,
    }
    (session_dir / "session.json").write_text(
        json.dumps(session, indent=2), encoding="utf-8"
    )
    (session_dir / "summary.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )

    total_bytes = sum(r["bytes"] for r in results)
    print(f"\nTotal bytes over all combinations: {total_bytes}")
    ranked = sorted(results, key=lambda r: r["score"], reverse=True)
    for result in ranked[:3]:
        if result["bytes"] == 0:
            break
        print(
            f"\nTop: {result['baud']} {result['format']} score {result['score']}"
        )
        print(f"  preview hex  : {result['preview_hex']}")
        print(f"  preview ascii: {result['preview_ascii']}")
        print(f"  shapes       : {result['shapes'] or '-'}")
        for hit in result["checksum_hits"]:
            print(f"  checksum     : {hit}")
    print(f"Saved {session_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
