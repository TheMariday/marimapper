from marimapper.led_identifier import find_led_in_image, draw_led_detections
from marimapper.camera import Camera


def close(x, y):
    return abs(x - y) < 0.000001


def test_basic_image_loading():

    mock_camera = Camera("test/MariMapper-Test-Data/9_point_box/cam_0/capture_0000.png")

    detection = find_led_in_image(mock_camera.read(color=False))
    assert close(detection.u, 0.4029418361244019)
    assert close(detection.v, 0.4029538809144072)


def test_none_found():

    mock_camera = Camera("test/MariMapper-Test-Data/9_point_box/cam_0/capture_%04d.png")

    for frame_id in range(24):
        frame = mock_camera.read(color=False)
        if frame_id in [7, 15, 23]:
            led_results = find_led_in_image(frame)
            assert led_results is None


def test_draw_results():

    mock_camera = Camera("test/MariMapper-Test-Data/9_point_box/cam_0/capture_%04d.png")
    frame = mock_camera.read()
    led_results = find_led_in_image(frame)
    draw_led_detections(frame, led_results)
