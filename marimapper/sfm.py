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
    return []