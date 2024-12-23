import os
from pathlib import Path
from marimapper.pycolmap_tools.read_write_model import (
    qvec2rotmat,
    read_images_binary,
    read_points3D_binary,
)

from marimapper.led import LED3D, View
from marimapper.led import remove_duplicates


def binary_to_led_map_3d(path: Path) -> list[LED3D]:

    points_bin = read_points3D_binary(os.path.join(path, "0", "points3D.bin"))
    images_bin = read_images_binary(os.path.join(path, "0", "images.bin"))

    views = {}
    leds = []

    for img in images_bin.values():

        rotation = qvec2rotmat(img.qvec).T
        translation = -rotation @ img.tvec

        views[img.id] = (img.id, translation, rotation)

    for (
        led_data
    ) in points_bin.values():  # this will overwrite previous data! needs filtering
        led_id = led_data.point2D_idxs[0]

        led = LED3D(led_id)

        led.point.position = led_data.xyz
        led.point.error = led_data.error
        led.views = [View(*views[view_id]) for view_id in led_data.image_ids]

        leds.append(led)

    leds = remove_duplicates(leds)

    return leds
