from itertools import combinations
from math import radians, tan

import numpy as np

from marimapper.database import COLMAPDatabase


def populate(db_path, led_maps_2d):
    if not led_maps_2d:
        raise Exception(
            "Failed to populate reconstruction database due to no maps being provided"
        )

    map_features = np.zeros((len(led_maps_2d), 1, 2))

    for map_index, led_map_2d in enumerate(led_maps_2d):

        for led_index in led_map_2d.led_indexes():

            pad_needed = led_index - map_features.shape[1] + 1
            if pad_needed > 0:
                map_features = np.pad(map_features, [(0, 0), (0, pad_needed), (0, 0)])

            map_features[map_index][led_index] = (
                np.array(led_map_2d.get_detection(led_index).pos()) * 2000
            )

    db = COLMAPDatabase.connect(db_path)

    db.create_tables()

    # model=0 means that it's a "SIMPLE PINHOLE" with just 1 focal length parameter that I think should get optimised
    # the params here should be f, cx, cy

    width = 2000
    height = 2000
    fov = 60  # degrees, this gets optimised so doesn't //really// matter that much

    SIMPLE_PINHOLE = 0

    cx = width / 2
    cy = height / 2
    f = (width / 2.0) / tan(radians(fov / 2.0))

    camera_id = db.add_camera(
        model=SIMPLE_PINHOLE, width=width, height=height, params=(f, cx, cy)
    )

    # Create dummy images_all_the_same.

    image_ids = [db.add_image(str(i), camera_id) for i in range(len(led_maps_2d))]

    # Create some keypoints
    for i, keypoints in enumerate(map_features):
        db.add_keypoints(image_ids[i], keypoints)

    for view_1_id, view_2_id in combinations(range(len(led_maps_2d)), 2):
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
