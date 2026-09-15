# Grab one frame from the Logitech C920 to confirm it sees the controller screen (one-off diagnostic).
"""Select the webcam by DirectShow name, not by index, and save a single frame.

The host also exposes laptop and virtual cameras, so index 0 is not the C920.
pygrabber enumerates DirectShow inputs in the same order OpenCV's CAP_DSHOW
backend uses, which lets us map a device name to an OpenCV index.
"""

import argparse
import sys
import time
from pathlib import Path

import cv2
from pygrabber.dshow_graph import FilterGraph

device_keyword = "C920"
warmup_frames = 30
target_width = 1920
target_height = 1080


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--keyword", default=device_keyword)
    args = parser.parse_args()

    names = FilterGraph().get_input_devices()
    for index, name in enumerate(names):
        print(f"[{index}] {name}")

    matches = [i for i, n in enumerate(names) if args.keyword in n]
    if not matches:
        print(f"No DirectShow device matches '{args.keyword}'.")
        return 1
    index = matches[0]
    print(f"Using index {index}: {names[index]}")

    capture = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if not capture.isOpened():
        print("OpenCV could not open the device (held by another app?).")
        return 1
    try:
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, target_width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, target_height)
        # Discard early frames so auto exposure and white balance settle.
        start = time.monotonic()
        for _ in range(warmup_frames):
            capture.read()
        ok, frame = capture.read()
        elapsed = time.monotonic() - start
    finally:
        capture.release()

    if not ok or frame is None:
        print("Device opened but returned no frame.")
        return 1

    height, width = frame.shape[:2]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(args.out), frame)
    print(
        f"Frame {width}x{height}, mean intensity {frame.mean():.1f}, "
        f"{warmup_frames + 1} reads in {elapsed:.2f} s"
    )
    print(f"Saved {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
