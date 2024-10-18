import os

from marimapper.pycolmap_tools.read_write_model import (
    qvec2rotmat,
    read_images_binary,
    read_points3D_binary,
)

from marimapper.led import LED3D, remove_duplicates


def binary_to_led_map_3d(path: os.path) -> list[LED3D]:

    points_bin = read_points3D_binary(os.path.join(path, "0", "points3D.bin"))

    leds: list[LED3D] = []

    for (
        led_data
    ) in points_bin.values():  # this will overwrite previous data! needs filtering
        led_id = led_data.point2D_idxs[0]

        led = LED3D(led_id)

        led.point.position = led_data.xyz
        led.point.error = led_data.error
        led.views = led_data.image_ids

        leds.append(led)

    leds = remove_duplicates(leds)

    return leds


class ReconstructedCamera:
    def __init__(self, camera_id, translation, rotation):
        self.camera_id = camera_id
        self.rotation = rotation
        self.translation = translation


def binary_to_cameras(path: os.path) -> list[ReconstructedCamera]:

    cameras = []

    images_bin = read_images_binary(os.path.join(path, "0", "images.bin"))

    for img in images_bin.values():

        rotation = qvec2rotmat(img.qvec).T
        translation = -rotation @ img.tvec

        camera = ReconstructedCamera(img.id, translation, rotation)

        cameras.append(camera)

    return cameras
