import pytest
from marimapper.camera import Camera


def test_valid_device():

    cam = Camera("test/MariMapper-Test-Data/9_point_box/cam_0/capture_0000.png")

    image = cam.read()

    assert image.shape == (480, 640)  # Grey

    image_bw = cam.read(color=True)

    assert image_bw.shape == (480, 640, 4)  # RGBA


def test_invalid_device():

    with pytest.raises(RuntimeError):
        Camera(device_id="bananas")
