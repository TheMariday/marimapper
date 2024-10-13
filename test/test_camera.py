import pytest
from marimapper.camera import Camera


def test_valid_device():

    cam = Camera("test/MariMapper-Test-Data/9_point_box/cam_0/capture_%04d.png")

    image = cam.read()

    assert image.shape == (480, 640)  # Grey

    image_colour = cam.read(color=True)

    assert image_colour.shape[2] >= 3 # sometimes there are 3 channels, sometimes 4 depending on platform?


def test_invalid_device():

    with pytest.raises(RuntimeError):
        Camera(device_id="bananas")
