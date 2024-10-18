import os

from tempfile import TemporaryDirectory
import pycolmap

from marimapper.database_populator import populate_database
from marimapper.model import binary_to_led_map_3d
from marimapper.utils import SupressLogging
from marimapper import logging


def sfm(maps_2d):
    logging.debug("SFM process starting sfm process")
    if len(maps_2d) < 2:
        logging.debug("SFM process failed to run sfm process as not enough maps")
        return None

    with TemporaryDirectory() as temp_dir:
        database_path = os.path.join(temp_dir, "database.db")

        populate_database(database_path, maps_2d)

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
            logging.debug(
                "SFM process failed to run sfm process as reconstruction failed"
            )
            return None

        logging.debug("SFM process finished sfm process")
        return binary_to_led_map_3d(temp_dir)
