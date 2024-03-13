import numpy as np
import os
from lib.sfm.read_write_model import (
    qvec2rotmat,
    read_cameras_binary,
    read_images_binary,
    read_points3D_binary,
)


def get_map_and_cams(path):

    led_map = []

    points_bin = read_points3D_binary(os.path.join(path, "0", "points3D.bin"))

    for point in points_bin.values():

        led_map.append({
            "index": point.point2D_idxs[0],
            "x": point.xyz[0],
            "y": point.xyz[1],
            "z": point.xyz[2],
            "error": point.error,
        })

    center_x = np.average([led["x"] for led in led_map])
    center_y = np.average([led["y"] for led in led_map])
    center_z = np.average([led["z"] for led in led_map])

    for i in range(len(led_map)):
        led_map[i]["x"] -= center_x
        led_map[i]["y"] -= center_y
        led_map[i]["z"] -= center_z

    # This is very gross and needs cleanup.
    # I think the maps need to be changed from a list to a dict

    led_map_merged = {}

    for led in led_map:
        if led["index"] not in led_map_merged:
            led_map_merged[led["index"]] = [led]
        else:
            led_map_merged[led["index"]].append(led)

    led_map = []
    for led_id in led_map_merged:
        x = np.average([led["x"] for led in led_map_merged[led_id]])
        y = np.average([led["y"] for led in led_map_merged[led_id]])
        z = np.average([led["z"] for led in led_map_merged[led_id]])
        e = np.sum([led["error"] for led in led_map_merged[led_id]])

        led_map.append({
            "index": led_id,
            "x": x,
            "y": y,
            "z": z,
            "error": e,
        })
    cams = []

    cameras_bin = read_cameras_binary(os.path.join(path, "0", "cameras.bin"))
    images_bin = read_images_binary(os.path.join(path, "0", "images.bin"))

    for img in images_bin.values():
        # rotation
        R = qvec2rotmat(img.qvec)

        # translation
        t = img.tvec

        # invert
        t = -R.T @ t
        R = R.T

        t[0] -= center_x
        t[1] -= center_y
        t[2] -= center_z

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

    return led_map, cams
