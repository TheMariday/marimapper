import os

from tempfile import TemporaryDirectory
import pycolmap

from marimapper.database_populator import populate_database
from marimapper.led import LED3D
from marimapper.model import binary_to_led_map_3d
from marimapper.utils import SupressLogging


def sfm(leds) -> list[LED3D]:

    with TemporaryDirectory() as temp_dir:
        database_path = os.path.join(temp_dir, "database.db")

        populate_database(database_path, leds)

        options = pycolmap.IncrementalPipelineOptions()
        options.triangulation.ignore_two_view_tracks = False  # used to be true
        options.min_num_matches = 9  # default 15
        options.mapper.abs_pose_min_num_inliers = 9  # default 30
        options.mapper.init_min_num_inliers = 50  # used to be 100

        with SupressLogging():
            pycolmap.incremental_mapping(
                database_path=database_path,
                image_path=temp_dir,
                output_path=temp_dir,
                options=options,
            )

        if not os.path.exists(os.path.join(temp_dir, "0", "points3D.bin")):
            return []

        leds = binary_to_led_map_3d(temp_dir)
        print(f"sfm managed to reconstruct {len(leds)} leds")
        return leds
