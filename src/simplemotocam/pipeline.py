"""Frame -> optional per-channel filters -> temporal/synthetic channels -> edges."""
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
import numpy as np
from .algebra import ChannelExpression, standard_channels
from .channels import (ChannelFrame, ConfidenceEstimator, Plane, checked_plane,
                       exposure_confidence, frozen_array)
from .operators import PlaneOperator


@dataclass(frozen=True)
class PipelineResult:
    frame: ChannelFrame
    channels: Mapping[str, Plane]
    differences: Mapping[str, Plane]
    synthetic: Mapping[str, Plane]
    edges: Mapping[str, Plane]
    temporal_ready: bool


class ChannelPipeline:
    def __init__(self, *, confidence: ConfidenceEstimator = exposure_confidence,
                 filters: Sequence[PlaneOperator] = (),
                 algebra: Mapping[str, ChannelExpression] | None = None,
                 edges: Mapping[str, PlaneOperator] | None = None):
        self.confidence = confidence
        self.filters = tuple(filters)
        self.algebra = dict(algebra or {})
        self.edge_estimators = dict(edges or {})
        self._previous: dict[str, Plane] | None = None

    def reset(self) -> None:
        """Call after changing source, calibration, or operator configuration."""
        self._previous = None

    def process(self, image: np.ndarray, *, order: str = "BGR") -> PipelineResult:
        frame = ChannelFrame.from_array(image, order=order, confidence=self.confidence)
        shape = frame.rgb.shape[:2]
        channels = frame.planes()
        for name in "RGB":
            for operator in self.filters:
                channels[name] = checked_plane(operator(channels[name]), shape, name)
        # A always describes the original acquisition, before filtering.
        previous = self._previous
        ready = previous is not None and previous["R"].shape == shape
        delta = ({f"d{name}": frozen_array(plane - previous[name])
                  for name, plane in channels.items()} if ready else {})
        context = {**channels, **delta}
        synthetic = {name: checked_plane(value, shape, name)
                     for name, value in standard_channels(context).items()}
        context.update(synthetic)
        for name, expression in self.algebra.items():
            if name in context:
                raise ValueError(f"Channel already exists: {name}")
            value = checked_plane(expression(MappingProxyType(context)), shape, name)
            synthetic[name] = value
            context[name] = value
        edge_planes = {}
        for name, estimator in self.edge_estimators.items():
            if name not in context:
                raise ValueError(f"Edge input unavailable: {name}")
            edge_planes[name] = checked_plane(estimator(context[name]), shape, name)
        # Commit history only after all operators succeed. Snapshot reused buffers.
        self._previous = {name: frozen_array(value) for name, value in channels.items()}
        return PipelineResult(frame, MappingProxyType(channels), MappingProxyType(delta),
                              MappingProxyType(synthetic), MappingProxyType(edge_planes), ready)
