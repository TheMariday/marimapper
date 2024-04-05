import os

import numpy as np

from lib.sfm.read_write_model import (
    qvec2rotmat,
    read_cameras_binary,
    read_images_binary,
    read_points3D_binary,
)
from lib.remesher import fix_normals


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

    cams = []

    cameras_bin = read_cameras_binary(os.path.join(path, "0", "cameras.bin"))
    images_bin = read_images_binary(os.path.join(path, "0", "images.bin"))

    camera_positions = {}

    for img in images_bin.values():
        # rotation
        R = qvec2rotmat(img.qvec)

        # translation
        t = img.tvec

        # invert
        t = -R.T @ t
        R = R.T

        t -= center

        camera_positions[img.id] = t

        # intrinsics
        cam = cameras_bin[img.camera_id]

        if cam.model in ("SIMPLE_PINHOLE", "SIMPLE_RADIAL", "RADIAL"):
            fx = fy = cam.params[0]
            cx = cam.params[1]
            cy = cam.params[2]
        elif cam.model in (
            "PINHOLE",
            "OPENCV",
            "OPENCV_FISHEYE",
            "FULL_OPENCV",
        ):
            fx = cam.params[0]
            fy = cam.params[1]
            cx = cam.params[2]
            cy = cam.params[3]
        else:
            raise Exception("Camera model not supported")

        # intrinsics
        K = np.identity(3)
        K[0, 0] = fx
        K[1, 1] = fy
        K[0, 2] = cx
        K[1, 2] = cy

        cams.append([K, R, t, cam.width, cam.height])

    for led_id in led_map:
        all_views = np.array(
            [camera_positions[view] for view in led_map[led_id]["views"]]
        )
        led_map[led_id]["normal"] = (
            np.average(all_views, axis=0) - led_map[led_id]["pos"]
        )

    led_map = fix_normals(led_map)

    return led_map, cams
