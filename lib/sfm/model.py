import numpy as np
import os
from lib.sfm.read_write_model import (
    qvec2rotmat,
    read_cameras_binary,
    read_images_binary,
    read_points3D_binary,
)


class Model:
    def __init__(self, path):
        self.cameras = read_cameras_binary(os.path.join(path, "cameras.bin"))
        self.images = read_images_binary(os.path.join(path, "images.bin"))
        self.points3D = read_points3D_binary(os.path.join(path, "points3D.bin"))

        self.points = {}

        self.cams = []

        self.center = []

        for point3D in self.points3D.values():

            point_id = point3D.point2D_idxs[0]
            if point_id > 23:
                continue

            self.points[point3D.point2D_idxs[0]] = {
                "pos": point3D.xyz,
                "error": point3D.error,
                "views": sorted(point3D.image_ids),
            }

        center_x = np.average([self.points[led_id]["pos"][0] for led_id in self.points])
        center_y = np.average([self.points[led_id]["pos"][1] for led_id in self.points])
        center_z = np.average([self.points[led_id]["pos"][2] for led_id in self.points])

        for led_id in self.points:
            self.points[led_id]["pos"][0] -= center_x
            self.points[led_id]["pos"][1] -= center_y
            self.points[led_id]["pos"][2] -= center_z

        for img in self.images.values():
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
            cam = self.cameras[img.camera_id]

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

            self.cams.append([K, R, t, cam.width, cam.height])
