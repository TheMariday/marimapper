from itertools import combinations
from math import radians, tan
from pathlib import Path
from multiprocessing import get_logger
import numpy as np

from marimapper.pycolmap_tools.database import COLMAPDatabase
from marimapper.led import LED2D, get_view_ids, get_leds_with_view

ARBITRARY_SCALE = 2000
logger = get_logger()


class CameraModel:

    SimplePinhole = 0  # f, cx, cy
    Pinhole = 1
    SimpleRadial = 2  # f, cx, cy k
    Radial = 3
    OpenCV = 4  # fx, fy, cx, cy, k1, k2, p1, p2
    OpenCVFisheye = 5
    FullOpenCV = 6
    FOV = 7
    SimpleRadialFisheye = 8
    RadialFisheye = 9
    ThinPrismFisheye = 10
    RadTanThinPrismFisheye = 11


def populate_database(db_path: Path, leds: list[LED2D]):
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

    # model=0 means that it's a "SIMPLE PINHOLE" with just 1 focal length parameter that I think should get optimised
    # the params here should be f, cx, cy

    width = ARBITRARY_SCALE
    height = ARBITRARY_SCALE
    fov = 60  # degrees, this gets optimised so doesn't //really// matter that much

    cx = width / 2
    cy = height / 2
    f = (width / 2.0) / tan(radians(fov / 2.0))

    camera_id = db.add_camera(
        model=CameraModel.SimpleRadial,
        width=width,
        height=height,
        params=(f, cx, cy, 0),
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
