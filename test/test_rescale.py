from marimapper.led import rescale
from marimapper.sfm import sfm
from marimapper.file_tools import get_all_2d_led_maps
from utils import get_test_dir


def test_rescale_basic():
    maps = get_all_2d_led_maps(get_test_dir("scan"))

    map_3d = sfm(maps)

    rescale(map_3d)
