import numpy as np
import pytest
from simplemotocam.channels import ChannelFrame, difference, exposure_confidence


def test_bgr_order_and_signed_difference_no_uint8_wraparound():
    before = ChannelFrame.from_array(np.array([[[10, 20, 250]]], np.uint8))
    after = ChannelFrame.from_array(np.array([[[30, 20, 5]]], np.uint8))
    assert before.planes()["R"][0, 0] == pytest.approx(250 / 255)
    delta = difference(after, before)
    assert delta["dR"][0, 0] == pytest.approx(-245 / 255)
    assert delta["dB"][0, 0] == pytest.approx(20 / 255)
    assert delta["dG"][0, 0] == 0


@pytest.mark.parametrize("order,pixel", [
    ("RGB", [1, 2, 3]), ("BGR", [3, 2, 1]),
    ("RGBA", [1, 2, 3, 0]), ("BGRA", [3, 2, 1, 0])])
def test_orders_and_opacity_is_not_confidence(order, pixel):
    frame = ChannelFrame.from_array(np.array([[pixel]], np.uint8), order=order,
                                   confidence=lambda rgb: np.ones(rgb.shape[:2]))
    np.testing.assert_allclose(frame.rgb[0, 0], np.array([1, 2, 3]) / 255)
    assert frame.confidence[0, 0] == 1
    if len(order) == 4:
        assert frame.opacity[0, 0] == 0


def test_uint16_and_float_normalization():
    image = np.array([[[0, 32768, 65535]]], np.uint16)
    frame = ChannelFrame.from_array(image, order="RGB")
    np.testing.assert_allclose(frame.rgb[0, 0], [0, 32768 / 65535, 1])
    np.testing.assert_allclose(
        ChannelFrame.from_array(frame.rgb, order="RGB").rgb, frame.rgb)


def test_exposure_confidence_known_values():
    rgb = np.array([[[0, .5, .5], [.025, .5, .5], [.5, .5, .5],
                     [1, .5, .5]]], np.float32)
    np.testing.assert_allclose(exposure_confidence(rgb), [[0, .5, 1, 0]])


@pytest.mark.parametrize("image", [
    np.zeros((2, 2)), np.zeros((0, 2, 3)), np.full((1, 1, 3), np.nan),
    np.full((1, 1, 3), 2.0), np.full((1, 1, 3), -0.1)])
def test_invalid_input_is_rejected(image):
    with pytest.raises(ValueError):
        ChannelFrame.from_array(image)


@pytest.mark.parametrize("estimate", [
    lambda rgb: np.ones((1, 1)), lambda rgb: np.full(rgb.shape[:2], np.inf),
    lambda rgb: np.full(rgb.shape[:2], 1.5)])
def test_invalid_confidence_is_rejected(estimate):
    with pytest.raises(ValueError):
        ChannelFrame.from_array(np.full((3, 4, 3), 100, np.uint8), confidence=estimate)


def test_frame_owns_read_only_snapshot():
    image = np.full((2, 2, 3), .5, np.float32)
    frame = ChannelFrame.from_array(image)
    image[:] = 0
    assert np.all(frame.rgb == .5)
    with pytest.raises(ValueError):
        frame.planes()["R"][0, 0] = 1
