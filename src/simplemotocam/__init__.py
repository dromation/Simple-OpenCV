"""SimpleOpenCV: explicit channels, signed differences, composable experiments."""
from .channels import ChannelFrame, exposure_confidence
from .pipeline import ChannelPipeline, PipelineResult

__all__ = ["ChannelFrame", "ChannelPipeline", "PipelineResult", "exposure_confidence"]
