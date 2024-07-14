from marimapper.led_identifier import LedFinder
from marimapper.camera import Camera


def close(x, y):
    return abs(x - y) < 0.000001


def test_init():
    LedFinder()


def test_basic_image_loading():
    led_finder = LedFinder()

    mock_camera = Camera("test/MariMapper-Test-Data/9_point_box/cam_0/capture_0000.png")

    detection = led_finder.find_led(mock_camera.read())
    assert close(detection.u, 0.4029418361244019)
    assert close(detection.v, 0.4029538809144072)


def test_none_found():
    led_finder = LedFinder()

    mock_camera = Camera("test/MariMapper-Test-Data/9_point_box/cam_0/capture_%04d.png")

    for frame_id in range(24):
        frame = mock_camera.read()
        if frame_id in [7, 15, 23]:
            led_results = led_finder.find_led(frame)
            assert led_results is None
