import os
from tempfile import TemporaryDirectory

import pycolmap

from lib.sfm.database_populator import populate
from lib.sfm.model import get_map_and_cams
from lib.utils import cprint, Col, SupressLogging
from lib import map_cleaner


class SFM:

    def __init__(self, maps):
        self.maps_2d = maps

        self.cams = None
        self.maps_3d = None
        self.mesh = None

    def process(self, rescale=False, interpolate=False):

        with TemporaryDirectory() as temp_dir:
            database_path = os.path.join(temp_dir, "database.db")

            populate(database_path, self.maps_2d)

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
                return False

            self.maps_3d, self.cams = get_map_and_cams(temp_dir)

            if rescale:
                map_cleaner.rescale(self.maps_3d, self.cams)

            if interpolate:
                leds_interpolated = map_cleaner.fill_gaps(self.maps_3d)
                cprint(f"Interpolated {leds_interpolated} leds", format=Col.BLUE)

            return True

    def print_points(self):
        for led_id in sorted(self.maps_3d.keys(), reverse=True):
            cprint(
                f"{led_id}:\t"
                f"x: {self.maps_3d[led_id]['pos'][0]}, "
                f"y: {self.maps_3d[led_id]['pos'][1]}, "
                f"z: {self.maps_3d[led_id]['pos'][2]}, "
                f"error: {self.maps_3d[led_id]['error']}",
                format=Col.BLUE,
            )

    def save_points(self, filename):
        self.maps_3d.write_to_file(filename)
