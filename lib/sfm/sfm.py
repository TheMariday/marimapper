import os

from tempfile import TemporaryDirectory
from pathlib import Path
import pycolmap
from multiprocessing import Process, Event

from lib.sfm.database_populator import populate
from lib.sfm.model import binary_to_led_map_3d
from lib.utils import SupressLogging
from lib import map_cleaner
from lib.led_map_2d import get_all_2d_led_maps
from lib import logging


class SFM(Process):

    def __init__(
        self,
        directory: Path,
        rescale=False,
        interpolate=False,
        event_on_update=None,
        led_map_2d_queue=None,
        led_map_3d_queue=None,
    ):
        logging.debug("SFM initialising")
        super().__init__()
        self.directory = directory
        self.rescale = rescale
        self.interpolate = interpolate
        self.exit_event = Event()
        self.reload_event = Event()
        self.event_on_update = event_on_update
        self.led_map_3d_queue = led_map_3d_queue
        self.led_map_2d_queue = led_map_2d_queue

        self.led_map_2d_queue.put(get_all_2d_led_maps(self.directory))

        logging.debug("SFM initialised")

    def add_led_maps_2d(self, maps):
        self.led_map_2d_queue.put(maps)

    def shutdown(self):
        logging.debug("SFM sending shutdown request")
        self.exit_event.set()

    def reload(self):
        logging.debug("SFM sending reload request")
        self.reload_event.set()

    def run(self):
        logging.debug("SFM process starting")
        self.reload__()
        while not self.exit_event.is_set():
            reload = self.reload_event.wait(timeout=1)
            if reload:
                self.reload__()

    def reload__(self):
        logging.debug("SFM process reloading")
        maps_2d = get_all_2d_led_maps(self.directory)
        if len(maps_2d) < 2:
            self.reload_event.clear()
            return None

        logging.debug(f"SFM process running on {len(maps_2d)} maps")

        map_3d = self.process__(maps_2d, self.rescale, self.interpolate)
        if map_3d is None or len(map_3d.keys()) == 0:
            self.reload_event.clear()
            return None

        map_3d.write_to_file(self.directory / "led_map_3d.csv")

        self.event_on_update.set()
        self.led_map_3d_queue.put(map_3d)
        self.reload_event.clear()
        logging.debug("SFM process reloaded")

    @staticmethod
    def process__(maps_2d, rescale=False, interpolate=False):
        logging.debug("SFM process starting sfm process")
        if len(maps_2d) < 2:
            logging.debug("SFM process failed to run sfm process as not enough maps")
            return None

        with TemporaryDirectory() as temp_dir:
            database_path = os.path.join(temp_dir, "database.db")

            populate(database_path, maps_2d)

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

            map_3d = binary_to_led_map_3d(temp_dir)

            if rescale:
                map_3d.rescale()

            if interpolate:
                leds_interpolated = map_cleaner.fill_gaps(map_3d)
                logging.debug(f"Interpolated {leds_interpolated} leds")

        logging.debug("SFM process finished sfm process")
        return map_3d
