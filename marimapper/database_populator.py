from itertools import combinations
from math import radians, tan
from pathlib import Path
from multiprocessing import get_logger
from typing import Union
import numpy as np

from marimapper.pycolmap_tools.database import COLMAPDatabase
from marimapper.led import LED2D, get_view_ids, get_leds_with_view

ARBITRARY_SCALE = 2000
logger = get_logger()


class CameraModel:
    def __init__(self, camera_model_id: int, args: list[any]):
        self.camera_model_id: int = camera_model_id
        self.camera_model_args: list[any] = args


# source of camera types etc:
# https://github.com/colmap/colmap/blob/main/src/colmap/sensor/models.h


def camera_model_pinhole(f: float, cx: float, cy: float) -> CameraModel:
    return CameraModel(0, [f, cx, cy])


def camera_model_radial(f: float, cx: float, cy: float) -> CameraModel:
    return CameraModel(2, [f, cx, cy] + [0])  # f, cx, cy, k


def camera_model_opencv(f: float, cx: float, cy: float) -> CameraModel:
    return CameraModel(4, [f, f, cx, cy] + [0] * 4)  # fx, fy, cx, cy, k1, k2, p1, p2


def camera_model_opencv_full(f: float, cx: float, cy: float) -> CameraModel:
    return CameraModel(
        6, [f, f, cx, cy] + [0] * 8
    )  # fx, fy, cx, cy, k1, k2, p1, p2, k3, k4, k5, k6


camera_models = [
    camera_model_pinhole,
    camera_model_radial,
    camera_model_opencv,
    camera_model_opencv_full,
]

camera_model_type = Union[*camera_models]


def populate_database(
    db_path: Path,
    leds: list[LED2D],
    camera_model_func: camera_model_type = camera_model_radial,
    fov_in_degrees: int = 60,
):
    logger.debug(f"Populating sfm database with {len(leds)} leds, path: {db_path}")
    views = get_view_ids(leds)
    map_features = np.zeros((max(views) + 1, 1, 2))

    for view in views:

        for led in get_leds_with_view(leds, view):

            pad_needed = led.led_id - map_features.shape[1] + 1
            if pad_needed > 0:
                map_features = np.pad(map_features, [(0, 0), (0, pad_needed), (0, 0)])

            # we flip this here so that the resulting 3D model is oriented with y+ up
            map_features[view][led.led_id] = (
                np.array((1 - led.point.position[0], 1 - led.point.position[1]))
                * ARBITRARY_SCALE
            )

    db = COLMAPDatabase.connect(db_path)

    db.create_tables()

    width = ARBITRARY_SCALE
    height = ARBITRARY_SCALE

    cx = width / 2
    cy = height / 2
    f = (width / 2.0) / tan(radians(fov_in_degrees / 2.0))

    camera_model = camera_model_func(f, cx, cy)

    camera_id = db.add_camera(
        model=camera_model.camera_model_id,
        width=width,
        height=height,
        params=camera_model.camera_model_args,
    )

    # Create dummy images_all_the_same.

    image_ids = [db.add_image(str(view), camera_id) for view in range(max(views) + 1)]

    # Create some keypoints
    for i, keypoints in enumerate(map_features):
        db.add_keypoints(image_ids[i], keypoints)

    for view_1_id, view_2_id in combinations(views, 2):
        view_1_keypoints = map_features[view_1_id]
        view_2_keypoints = map_features[view_2_id]

        shared_led_ids = []

        for i in range(len(view_1_keypoints)):
            in_both = view_1_keypoints[i].any() and view_2_keypoints[i].any()
            if in_both:
                shared_led_ids.append([i, i])

        if shared_led_ids:
            db.add_two_view_geometry(
                image_ids[view_1_id], image_ids[view_2_id], np.array(shared_led_ids)
            )

    db.commit()
    db.close()
