from pathlib import Path
from tempfile import TemporaryDirectory
import pycolmap

from marimapper.database_populator import populate_database
from marimapper.led import LED3D, LED2D, get_view_ids, get_leds
from marimapper.model import binary_to_led_map_3d
from marimapper.utils import SupressLogging
from multiprocessing import get_logger

logger = get_logger()


def sfm(leds_2d: list[LED2D]) -> list[LED3D]:

    # if no leds, don't bother
    if len(leds_2d) == 0:
        logger.debug("no leds :(")
        return []

    # also if we're just on 1 view, don't bother
    if len(get_view_ids(leds_2d)) <= 1:
        logger.debug("<= 1 view :(")
        return []

    with TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir, "database.db")

        populate_database(database_path, leds_2d)

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

        # NOTE!
        # There might be more map folders than just "0", however this is the base section and only the one we're
        # interested in at the moment. We could iterate through all avaliable maps
        # However I think it might be misleading or confusing as they will appear with no relative transform.
        # Because of this, lots of existing functionality like inter-led distance might break
        # Leaving it out for now but perhaps something to come back to.

        if not Path(temp_dir, "0", "points3D.bin").exists():
            return []

        leds_3d = binary_to_led_map_3d(Path(temp_dir))
        logger.debug(f"sfm managed to reconstruct {len(leds_3d)} leds")

        return leds_3d
