import numpy as np

from marimapper.sfm import sfm
from marimapper.file_tools import get_all_2d_led_maps
from marimapper.led import get_led, get_leds_with_views
from utils import get_test_dir


def check_dimensions(map_3d, max_error):
    cube_sides = []

    for start, end in (
        [2, 0],
        [4, 6],
        [18, 16],
        [20, 22],
        [4, 2],
        [20, 18],
        [6, 0],
        [22, 16],
        [16, 0],
        [18, 2],
        [20, 4],
        [22, 6],
    ):
        cube_sides.append(
            get_led(map_3d, start).point.position - get_led(map_3d, end).point.position
        )

    cube_side_lengths = [np.linalg.norm(v) for v in cube_sides]

    cube_side_length_avg = np.average(cube_side_lengths)

    cube_side_deviation = [
        length / cube_side_length_avg for length in cube_side_lengths
    ]

    assert max(cube_side_deviation) < 1 + max_error
    assert min(cube_side_deviation) > 1 - max_error


def test_reconstruction():
    maps = get_all_2d_led_maps(get_test_dir("scan"))

    map_3d = sfm(maps)

    assert len(map_3d) == 21

    check_dimensions(
        map_3d, max_error=0.01  # needs to have a max deviation of less than 1%
    )


def test_sparse_reconstruction():
    maps = get_all_2d_led_maps(get_test_dir("scan"))

    maps_sparse = get_leds_with_views(maps, [1, 3, 5, 7])

    map_3d = sfm(maps_sparse)

    assert len(map_3d) == 21

    check_dimensions(
        map_3d, max_error=0.03  # needs to have a max deviation of less than 3%
    )


def test_2_track_reconstruction():
    leds = get_all_2d_led_maps(get_test_dir("scan"))
    leds_2_track = get_leds_with_views(leds, [1, 2])

    map_3d = sfm(leds_2_track)

    assert len(map_3d) == 15


def test_invalid_reconstruction_views():
    leds = get_all_2d_led_maps(get_test_dir("scan"))

    leds_invalid = get_leds_with_views(leds, [0, 4, 8])

    map_3d = sfm(leds_invalid)

    assert map_3d == []
