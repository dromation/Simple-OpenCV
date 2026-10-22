"""Run a deterministic synthetic experiment, video file, or explicit camera."""
import argparse
from contextlib import ExitStack
import json
from pathlib import Path
import cv2
import numpy as np
from .capture import OpenCVCapture
from .operators import Gaussian, ScharrMagnitude, SobelMagnitude
from .pipeline import ChannelPipeline


def synthetic_frames(count: int, height: int = 120, width: int = 160):
    """A moving R-only patch; constant G/B reveal channel isolation."""
    for index in range(count):
        frame = np.full((height, width, 3), 96, dtype=np.uint8)  # BGR
        x = (index * 3) % (width - 24)
        frame[height // 3:height // 3 + 24, x:x + 24, 2] = 192
        yield frame


def preview(result):
    """Display conversion only: all scientific arrays keep their signed values."""
    h, w = result.frame.rgb.shape[:2]
    tiles = []
    views = [("RGB", result.frame.rgb[..., ::-1])]
    for index, name in enumerate("RGB"):
        color = np.zeros((h, w, 3), dtype=np.float32)
        color[..., 2 - index] = result.channels[name]
        views.append((name, color))
    views.extend([("A confidence", result.channels["A"]),
                  ("dR (zero=gray)", (result.differences.get("dR", np.zeros((h, w))) + 1) / 2),
                  ("R-G (zero=gray)", (result.synthetic["R-G"] + 1) / 2),
                  ("edges R-G", result.edges["R-G"])])
    for label, data in views:
        tile = np.uint8(np.clip(data, 0, 1) * 255)
        if tile.ndim == 2:
            tile = cv2.cvtColor(tile, cv2.COLOR_GRAY2BGR)
        tile = cv2.resize(tile, (320, 240))
        cv2.rectangle(tile, (0, 0), (320, 26), (20, 20, 20), -1)
        cv2.putText(tile, label, (8, 19), cv2.FONT_HERSHEY_SIMPLEX, .5,
                    (255, 255, 255), 1, cv2.LINE_AA)
        tiles.append(tile)
    return np.vstack([np.hstack(tiles[:4]), np.hstack(tiles[4:])])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--camera", type=int, help="Camera index; used only when supplied")
    source.add_argument("--video", type=Path, help="Read a video file")
    parser.add_argument("--frames", type=int, default=60)
    parser.add_argument("--show", action="store_true", help="Show channel panels; Esc or Q exits")
    parser.add_argument("--blur", type=float, default=0, help="Gaussian sigma; 0 disables")
    parser.add_argument("--edge", choices=["sobel", "scharr"], default="sobel")
    parser.add_argument("--output", type=Path, help="Write JSON summary (must not already exist)")
    args = parser.parse_args(argv)
    if args.frames < 1 or not np.isfinite(args.blur) or args.blur < 0:
        parser.error("--frames must be positive and --blur must be finite and nonnegative")
    if args.video is not None and not args.video.is_file():
        parser.error("--video must be an existing file")
    if args.camera is not None and args.camera < 0:
        parser.error("--camera must be nonnegative")
    if args.output is not None and args.output.exists():
        parser.error("--output already exists")
    pipeline = ChannelPipeline(
        filters=[Gaussian(args.blur)] if args.blur else [],
        edges={"R-G": SobelMagnitude() if args.edge == "sobel" else ScharrMagnitude()})
    peaks = dict.fromkeys(("dR", "dG", "dB", "dA"), 0.0)
    processed = pairs = 0
    try:
        with ExitStack() as stack:
            if args.camera is not None or args.video is not None:
                value = args.camera if args.camera is not None else str(args.video)
                frames = stack.enter_context(OpenCVCapture(value))
            else:
                frames = synthetic_frames(args.frames)
            for image in frames:
                result = pipeline.process(image)
                processed += 1
                pairs += int(result.temporal_ready)
                for name, plane in result.differences.items():
                    peaks[name] = max(peaks[name], float(np.abs(plane).max()))
                if args.show:
                    cv2.imshow("SimpleMotocam channel laboratory", preview(result))
                    if cv2.waitKey(30) & 0xFF in (27, ord("q")):
                        break
                if processed >= args.frames:
                    break
    finally:
        if args.show:
            cv2.destroyAllWindows()
    if processed == 0:
        raise RuntimeError("Source produced no readable frames")
    summary = {"source": ("camera" if args.camera is not None else
                          "video" if args.video is not None else "synthetic"),
               "frames": processed, "temporal_pairs": pairs,
               "max_abs_difference": peaks,
               "synthetic_channels": sorted(result.synthetic),
               "confidence": "Exposure headroom heuristic; not calibrated probability"}
    text = json.dumps(summary, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as out:
            out.write(text + "\n")
    print(text)
    return 0
