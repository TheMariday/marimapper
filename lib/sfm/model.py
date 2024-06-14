import os

import numpy as np

from lib.sfm.read_write_model import (
    qvec2rotmat,
    read_images_binary,
    read_points3D_binary,
)
from lib.remesher import fix_normals
from lib.led_map_3d import LEDMap3D


def binary_to_led_map_3d(path):
    led_map = {}

    points_bin = read_points3D_binary(os.path.join(path, "0", "points3D.bin"))

    for (
        point
    ) in points_bin.values():  # this will overwrite previous data! needs filtering
        led_id = point.point2D_idxs[0]
        if led_id not in led_map:
            led_map[point.point2D_idxs[0]] = {"pos": [], "error": [], "views": []}

        led_map[point.point2D_idxs[0]]["pos"].append(point.xyz)
        led_map[point.point2D_idxs[0]]["error"].append(point.error)
        led_map[point.point2D_idxs[0]]["views"].extend(point.image_ids)

    for led_id in led_map:
        led_map[led_id]["pos"] = np.average(led_map[led_id]["pos"], axis=0)
        led_map[led_id]["error"] = np.average(led_map[led_id]["error"], axis=0)
        led_map[led_id]["views"] = list(set(led_map[led_id]["views"]))

    translation_offset = np.average([led_map[led_id]["pos"] for led_id in led_map], axis=0)

    for led_id in led_map:
        led_map[led_id]["pos"] -= translation_offset

    cameras = []

    images_bin = read_images_binary(os.path.join(path, "0", "images.bin"))

    camera_positions = {}

    for img in images_bin.values():
        rotation = qvec2rotmat(img.qvec)

        translation = -rotation.T @ img.tvec
        rotation = rotation.T

        translation -= translation_offset

        camera_positions[img.id] = translation

        cameras.append([rotation, translation])

    for led_id in led_map:
        all_views = np.array(
            [camera_positions[view] for view in led_map[led_id]["views"]]
        )
        led_map[led_id]["normal"] = (
            np.average(all_views, axis=0) - led_map[led_id]["pos"]
        )

    led_map_3d = LEDMap3D(fix_normals(led_map))
    led_map_3d.cameras = cameras

    return led_map_3d
