# it's something in heeeere
from pathlib import Path
from tempfile import TemporaryDirectory
print("importing pycolmap")
import pycolmap
print("pycolmap imported!")
from marimapper.database_populator import (
    populate_database,
    camera_model_radial,
    camera_model_type,
)
from marimapper.led import LED3D, LED2D, get_view_ids
from marimapper.model import binary_to_led_map_3d
from marimapper.utils import SupressLogging
from multiprocessing import get_logger

logger = get_logger()


def sfm(
    leds_2d: list[LED2D],
    camera_model: camera_model_type = camera_model_radial,
    camera_fov: int = 60,
) -> list[LED3D]:
    # if no leds, don't bother
    if len(leds_2d) == 0:
        logger.debug("no leds :(")
        return []

    logger.debug("Reconstructing science...")

    # also if we're just on 1 view, don't bother
    if len(get_view_ids(leds_2d)) <= 1:
        logger.debug("<= 1 view :(")
        return []

    with TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir, "database.db")

        populate_database(database_path, leds_2d, camera_model, camera_fov)

        options = pycolmap.IncrementalPipelineOptions()
        options.triangulation.ignore_two_view_tracks = False  # used to be true
        options.min_num_matches = 9  # default 15
        options.mapper.abs_pose_min_num_inliers = 9  # default 30
        options.mapper.init_min_num_inliers = 50  # used to be 100

        # I think what's happening here is that this is spinning up a thread which is crashing the forked process https://github.com/python/cpython/issues/77906
        # Aaaah if this sig sevs then it got caught by the handler
        if True:
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

        leds_3d = []
        for map_id in range(0, 10):
            if not Path(temp_dir, f"{map_id}", "points3D.bin").exists():
                break

            new_map = binary_to_led_map_3d(Path(temp_dir))

            logger.debug(
                f"sfm managed to reconstruct {len(new_map)} leds in map {map_id}"
            )

            leds_3d = new_map if len(new_map) > len(leds_3d) else leds_3d

        return leds_3d
