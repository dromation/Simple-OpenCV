"""Channel values are normalized float32; A is a derived quality weight."""
from dataclasses import dataclass
from typing import Callable
import numpy as np
from numpy.typing import NDArray

Plane = NDArray[np.float32]
ConfidenceEstimator = Callable[[Plane], Plane]


def frozen_array(value: object) -> Plane:
    result = np.array(value, dtype=np.float32, copy=True)
    result.setflags(write=False)
    return result


def checked_plane(value: object, shape: tuple[int, int], name: str) -> Plane:
    result = np.asarray(value, dtype=np.float32)
    if result.shape != shape or not np.isfinite(result).all():
        raise ValueError(f"{name} must be a finite plane with shape {shape}")
    return frozen_array(result)


def exposure_confidence(rgb: Plane, margin: float = 0.05) -> Plane:
    """Heuristic headroom from clipping in ANY channel, not a probability.

    A = clip(min(R,G,B,1-R,1-G,1-B) / margin, 0, 1).
    It penalizes black/saturated pixels and is replaceable after calibration.
    """
    if not np.isfinite(margin) or not 0 < margin <= 0.5:
        raise ValueError("margin must be in (0, 0.5]")
    return np.clip(np.minimum(rgb, 1 - rgb).min(axis=2) / margin, 0, 1)


@dataclass(frozen=True)
class ChannelFrame:
    rgb: Plane
    confidence: Plane
    opacity: Plane | None = None

    def __post_init__(self) -> None:
        rgb = np.asarray(self.rgb, dtype=np.float32)
        if rgb.ndim != 3 or rgb.shape[2] != 3 or 0 in rgb.shape:
            raise ValueError("rgb must have nonempty shape (height, width, 3)")
        if not np.isfinite(rgb).all() or np.any((rgb < 0) | (rgb > 1)):
            raise ValueError("rgb must contain finite values in [0, 1]")
        object.__setattr__(self, "rgb", frozen_array(rgb))
        for name in ("confidence", "opacity"):
            value = getattr(self, name)
            if value is None and name == "opacity":
                continue
            plane = checked_plane(value, rgb.shape[:2], name)
            if np.any((plane < 0) | (plane > 1)):
                raise ValueError(f"{name} must be in [0, 1]")
            object.__setattr__(self, name, plane)

    @classmethod
    def from_array(cls, image: np.ndarray, *, order: str = "BGR",
                   confidence: ConfidenceEstimator = exposure_confidence) -> "ChannelFrame":
        """Accept uint8, uint16, or normalized float RGB/BGR/RGBA/BGRA.

        An input alpha byte is opacity only; it is kept separately from A.
        This does not linearize gamma-encoded camera RGB into radiance.
        """
        if order not in ("RGB", "BGR", "RGBA", "BGRA"):
            raise ValueError("order must be RGB, BGR, RGBA, or BGRA")
        image = np.asarray(image)
        if image.ndim != 3 or image.shape[2] != len(order) or 0 in image.shape:
            raise ValueError(f"Expected nonempty H x W x {len(order)} image")
        if image.dtype == np.uint8:
            values = image.astype(np.float32) / 255
        elif image.dtype == np.uint16:
            values = image.astype(np.float32) / 65535
        elif np.issubdtype(image.dtype, np.floating):
            values = image.astype(np.float32)
        else:
            raise TypeError("Use uint8, uint16, or normalized floating point input")
        if not np.isfinite(values).all() or np.any((values < 0) | (values > 1)):
            raise ValueError("Input must be finite and normalized to [0, 1]")
        rgb = frozen_array(values[..., :3][..., ::-1] if order.startswith("BGR")
                           else values[..., :3])
        opacity = values[..., 3] if len(order) == 4 else None
        return cls(rgb, confidence(rgb), opacity)

    def planes(self) -> dict[str, Plane]:
        return {"R": self.rgb[..., 0], "G": self.rgb[..., 1],
                "B": self.rgb[..., 2], "A": self.confidence}


def difference(current: ChannelFrame, previous: ChannelFrame) -> dict[str, Plane]:
    """Signed current - previous, including the derived confidence difference."""
    if current.rgb.shape != previous.rgb.shape:
        raise ValueError("Frames must have the same dimensions")
    old = previous.planes()
    return {f"d{name}": frozen_array(plane - old[name])
            for name, plane in current.planes().items()}
