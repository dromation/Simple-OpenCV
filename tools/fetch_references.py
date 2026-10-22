"""Fetch pinned historical reference checkouts without replacing existing files."""

import argparse
from pathlib import Path
import subprocess

SOURCES = {
    "opencv-2.4.13.7": (
        "https://github.com/opencv/opencv.git",
        "51cfa519249c89d24035b3f96315ad997deb300f",
    ),
    "ComputerVision-MachineVision": (
        "https://github.com/mech-id-x/ComputerVision-MachineVision.git",
        "2054108d00b46f3ee3070ed733d67a016b1ed918",
    ),
    "SI_Eksperimenti_Strojnega_Vida": (
        "https://github.com/mech-id-x/SI_Eksperimenti_Strojnega_Vida.git",
        "33ac150c0cf2205313dd91ce3eab511e12c38fe7",
    ),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", choices=sorted(SOURCES))
    args = parser.parse_args()
    target = Path(__file__).resolve().parents[1] / "external" / args.source
    if target.exists():
        parser.exit(0, f"Kept existing reference unchanged: {target}\n")
    target.mkdir(parents=True)
    url, revision = SOURCES[args.source]
    git = ["git", "-c", f"safe.directory={target.as_posix()}", "-C", str(target)]
    try:
        for command in [
            ["init"],
            ["remote", "add", "origin", url],
            ["fetch", "--depth", "1", "origin", revision],
            ["checkout", "--detach", "FETCH_HEAD"],
        ]:
            subprocess.run(git + command, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        parser.exit(
            1,
            f"Fetch failed: {exc}. Partial checkout retained for inspection: {target}\n",
        )
    print(
        f"Reference ready: {target}\nPinned commit: {revision}\nThis reference is not installed or executed."
    )


if __name__ == "__main__":
    main()
