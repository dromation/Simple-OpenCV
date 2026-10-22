"""Callable plugins: accept one float32 plane and return one finite same-size plane."""
from dataclasses import dataclass
from typing import Protocol
import cv2
import numpy as np
from .channels import Plane


class PlaneOperator(Protocol):
    def __call__(self, plane: Plane) -> Plane: ...


@dataclass(frozen=True)
class Gaussian:
    sigma: float = 1.0

    def __post_init__(self) -> None:
        if not np.isfinite(self.sigma) or self.sigma <= 0:
            raise ValueError("sigma must be positive and finite")

    def __call__(self, plane: Plane) -> Plane:
        return cv2.GaussianBlur(plane, (0, 0), self.sigma,
                               borderType=cv2.BORDER_REFLECT_101)


@dataclass(frozen=True)
class SobelMagnitude:
    """Spatial derivative magnitude, normalized for a 3x3 Sobel kernel."""
    def __call__(self, plane: Plane) -> Plane:
        dx = cv2.Sobel(plane, cv2.CV_32F, 1, 0, ksize=3, scale=1 / 8)
        dy = cv2.Sobel(plane, cv2.CV_32F, 0, 1, ksize=3, scale=1 / 8)
        return np.hypot(dx, dy)


@dataclass(frozen=True)
class ScharrMagnitude:
    def __call__(self, plane: Plane) -> Plane:
        dx = cv2.Scharr(plane, cv2.CV_32F, 1, 0, scale=1 / 32)
        dy = cv2.Scharr(plane, cv2.CV_32F, 0, 1, scale=1 / 32)
        return np.hypot(dx, dy)
