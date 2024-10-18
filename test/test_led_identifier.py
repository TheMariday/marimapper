import pytest

from marimapper.detector import find_led_in_image, draw_led_detections
from marimapper.camera import Camera


def test_basic_image_loading():

    mock_camera = Camera("MariMapper-Test-Data/9_point_box/cam_0/capture_0000.png")

    detection = find_led_in_image(mock_camera.read())
    assert detection.u() == pytest.approx(0.4029418361244019)
    assert detection.v() == pytest.approx(0.4029538809144072)


def test_none_found():

    mock_camera = Camera("MariMapper-Test-Data/9_point_box/cam_0/capture_%04d.png")

    for frame_id in range(24):
        frame = mock_camera.read()
        if frame_id in [7, 15, 23]:
            led_detection = find_led_in_image(frame)
            assert led_detection is None


def test_draw_results():

    mock_camera = Camera("MariMapper-Test-Data/9_point_box/cam_0/capture_%04d.png")
    frame = mock_camera.read()
    led_detection = find_led_in_image(frame)
    draw_led_detections(frame, led_detection)
