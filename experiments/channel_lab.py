"""Run after installing the local package: python experiments/channel_lab.py."""
import numpy as np
from simplemotocam import ChannelPipeline
from simplemotocam.cli import synthetic_frames
from simplemotocam.operators import Gaussian, ScharrMagnitude


def main():
    pipeline = ChannelPipeline(
        filters=[Gaussian(0.8)],
        algebra={
            "red_opponent": lambda c: c["R"] - (c["G"] + c["B"]) / 2,
            "temporal_opponent": lambda c: (
                c["dR"] - c["dB"] if "dR" in c else np.zeros_like(c["R"])),
        },
        edges={"red_opponent": ScharrMagnitude()},
    )
    for index, frame in enumerate(synthetic_frames(5)):
        result = pipeline.process(frame)
        print(index, "ready:", result.temporal_ready,
              "peak change:", float(np.abs(result.synthetic["temporal_opponent"]).max()))


if __name__ == "__main__":
    main()
