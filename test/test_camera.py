import pytest
from marimapper.camera import Camera


def test_valid_device():

    cam = Camera("test/MariMapper-Test-Data/9_point_box/cam_0/capture_%04d.png")

    image = cam.read()

    assert image.shape[0] == 480
    assert image.shape[1] == 640
    assert image.shape[2] >= 3


def test_invalid_device():

    with pytest.raises(RuntimeError):
        Camera(device_id="bananas")
