import numpy as np
import pytest
from simplemotocam import ChannelPipeline
from simplemotocam.operators import Gaussian, SobelMagnitude, ScharrMagnitude
from simplemotocam.cli import main, synthetic_frames, preview


def test_temporal_priming_channel_isolation_and_synthetic_algebra():
    pipe = ChannelPipeline(algebra={"custom": lambda c: 2 * c["R"] - c["B"]})
    frames = list(synthetic_frames(2))
    first = pipe.process(frames[0])
    second = pipe.process(frames[1])
    assert not first.temporal_ready and not first.differences
    assert "motion" not in first.synthetic
    assert second.temporal_ready
    assert np.max(second.differences["dR"]) == pytest.approx(96 / 255)
    assert np.min(second.differences["dR"]) == pytest.approx(-96 / 255)
    assert not np.any(second.differences["dG"])
    assert not np.any(second.differences["dB"])
    np.testing.assert_allclose(second.synthetic["dR-dB"], second.differences["dR"])
    np.testing.assert_allclose(second.synthetic["motion"], abs(second.differences["dR"]))
    np.testing.assert_allclose(second.synthetic["custom"],
                               2 * second.channels["R"] - second.channels["B"])


def test_confident_motion_requires_both_frames_usable():
    pipe = ChannelPipeline()
    pipe.process(np.zeros((3, 3, 3), np.uint8))
    result = pipe.process(np.full((3, 3, 3), 128, np.uint8))
    assert result.synthetic["motion"].max() > 0
    assert result.synthetic["confident_motion"].max() == 0


def test_reset_and_resolution_change_prime_history():
    pipe = ChannelPipeline()
    image = np.full((4, 4, 3), 128, np.uint8)
    pipe.process(image)
    assert pipe.process(image).temporal_ready
    pipe.reset()
    assert not pipe.process(image).temporal_ready
    assert not pipe.process(image[:2]).temporal_ready


def test_reused_capture_buffer_cannot_modify_previous_frame():
    pipe = ChannelPipeline()
    image = np.full((3, 3, 3), 100, np.uint8)
    pipe.process(image)
    image[..., 2] = 200
    np.testing.assert_allclose(pipe.process(image).differences["dR"], 100 / 255)


@pytest.mark.parametrize("edge", [SobelMagnitude(), ScharrMagnitude()])
def test_edges_detect_vertical_step_and_zero_on_constant(edge):
    plane = np.zeros((12, 12), np.float32)
    plane[:, 6:] = 1
    response = edge(plane)
    assert response[:, 5:7].min() == pytest.approx(.5)
    assert np.all(response[:, :4] == 0)
    assert np.all(edge(np.ones((12, 12), np.float32)) == 0)


def test_custom_filters_edges_and_ordered_algebra():
    image = np.full((4, 4, 3), 128, np.uint8)
    pipe = ChannelPipeline(filters=[lambda p: p * 2],
        algebra={"sum": lambda c: c["R"] + c["G"],
                 "half_sum": lambda c: c["sum"] / 2},
        edges={"half_sum": lambda p: p + 1})
    result = pipe.process(image)
    np.testing.assert_allclose(result.synthetic["half_sum"], 256 / 255)
    np.testing.assert_allclose(result.edges["half_sum"], 256 / 255 + 1)
    assert result.frame.rgb.max() < 1  # Original acquisition remains available.


@pytest.mark.parametrize("operator", [lambda p: p[:1], lambda p: p * np.nan])
def test_invalid_plugin_does_not_commit_history(operator):
    pipe = ChannelPipeline(filters=[operator])
    with pytest.raises(ValueError):
        pipe.process(np.full((4, 4, 3), 128, np.uint8))
    pipe.filters = ()
    assert not pipe.process(np.full((4, 4, 3), 128, np.uint8)).temporal_ready


def test_channel_collision_is_rejected():
    with pytest.raises(ValueError, match="already exists"):
        ChannelPipeline(algebra={"R": lambda c: c["B"]}).process(
            np.zeros((4, 4, 3), np.uint8))


def test_gaussian_reduces_impulse_and_preserves_constant():
    operator = Gaussian(1)
    plane = np.zeros((15, 15), np.float32)
    plane[7, 7] = 1
    blurred = operator(plane)
    assert 0 < blurred[7, 7] < 1
    assert blurred.sum() == pytest.approx(1)
    np.testing.assert_allclose(operator(np.full((15, 15), .3, np.float32)), .3, atol=1e-7)


def test_headless_cli_and_preview(tmp_path, capsys):
    output = tmp_path / "summary.json"
    assert main(["--frames", "3", "--output", str(output)]) == 0
    import json
    report = json.loads(output.read_text())
    assert report["frames"] == 3 and report["temporal_pairs"] == 2
    assert report["max_abs_difference"]["dG"] == 0
    with pytest.raises(SystemExit):
        main(["--output", str(output)])
    pipe = ChannelPipeline(edges={"R-G": SobelMagnitude()})
    assert preview(pipe.process(next(synthetic_frames(1)))).shape == (480, 1280, 3)
