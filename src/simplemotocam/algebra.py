"""Ordinary Python callables compose channel algebra; no string evaluation."""
from collections.abc import Callable, Mapping
import numpy as np
from .channels import Plane

ChannelMap = Mapping[str, Plane]
ChannelExpression = Callable[[ChannelMap], Plane]


def standard_channels(channels: ChannelMap) -> dict[str, Plane]:
    result = {"R-G": channels["R"] - channels["G"],
              "G-B": channels["G"] - channels["B"]}
    if "dR" in channels:
        result["dR-dB"] = channels["dR"] - channels["dB"]
        magnitude = np.sqrt(sum(channels[f"d{c}"] ** 2 for c in "RGB"))
        result["motion"] = magnitude
        # Both frames must be usable; A_previous is reconstructed from dA.
        pair_confidence = np.minimum(channels["A"], channels["A"] - channels["dA"])
        result["confident_motion"] = pair_confidence * magnitude
    return result
