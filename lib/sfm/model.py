import os

import numpy as np

from lib.sfm.read_write_model import (
    qvec2rotmat,
    read_images_binary,
    read_points3D_binary,
)
from lib.remesher import fix_normals
from lib.led_map_3d import LEDMap3D
from lib.camera_map_3d import CameraMap3D


def get_map_and_cams(path):
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

    center = np.average([led_map[led_id]["pos"] for led_id in led_map], axis=0)

    for led_id in led_map:
        led_map[led_id]["pos"] -= center

    cams = CameraMap3D()

    images_bin = read_images_binary(os.path.join(path, "0", "images.bin"))

    for img in images_bin.values():
        # rotation
        R = qvec2rotmat(img.qvec)

        # translation
        t = img.tvec

        # invert
        t = -R.T @ t

        t -= center

        cams.add_cam(img.id, t, img.qvec)

    for led_id in led_map:
        all_views = np.array(
            [cams.get_cam(view)["position"] for view in led_map[led_id]["views"]]
        )
        led_map[led_id]["normal"] = (
            np.average(all_views, axis=0) - led_map[led_id]["pos"]
        )

    led_map = fix_normals(led_map)

    return LEDMap3D(led_map), cams
