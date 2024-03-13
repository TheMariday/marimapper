import sys
import pytest
import numpy as np

sys.path.append("./")
from lib.sfm.sfm import SFM
from lib.map_read_write import get_all_maps


def check_dimensions(map_3d, max_error):

    led_remap = {}

    for led in map_3d:
        led_remap[led["index"]] = np.array((led["x"], led["y"], led["z"]))

    cube_sides = []
    cube_sides.append(led_remap[2] - led_remap[0])
    cube_sides.append(led_remap[4] - led_remap[6])
    cube_sides.append(led_remap[18] - led_remap[16])
    cube_sides.append(led_remap[20] - led_remap[22])

    cube_sides.append(led_remap[4] - led_remap[2])
    cube_sides.append(led_remap[20] - led_remap[18])
    cube_sides.append(led_remap[6] - led_remap[0])
    cube_sides.append(led_remap[22] - led_remap[16])

    cube_sides.append(led_remap[16] - led_remap[0])
    cube_sides.append(led_remap[18] - led_remap[2])
    cube_sides.append(led_remap[20] - led_remap[4])
    cube_sides.append(led_remap[22] - led_remap[6])

    cube_side_lengths = [np.linalg.norm(v) for v in cube_sides]

    cube_side_length_avg = np.average(cube_side_lengths)

    cube_side_deviation = [
        length / cube_side_length_avg for length in cube_side_lengths
    ]

    assert max(cube_side_deviation) < 1 + max_error
    assert min(cube_side_deviation) > 1 - max_error


def test_reconstruction():

    maps = get_all_maps("test/scan")

    sfm = SFM(maps)

    sfm.process()

    sfm.print_points()

    assert len(sfm.maps_3d) == 21

    check_dimensions(
        sfm.maps_3d, max_error=0.01  # needs to have a max deviation of less than 1%
    )


# remove for now
"""
def test_sparse_reconstruction():

    maps = get_all_maps("test/scan")

    maps_sparse = [maps[1], maps[3], maps[5], maps[7]]

    sfm = SFM(maps_sparse)

    sfm.process()

    sfm.print_points()

    assert len(sfm.maps_3d) == 21

    check_dimensions(
        sfm.maps_3d, max_error=0.03  # needs to have a max deviation of less than 3%
    )
"""

""" # this doesn't work on ubuntu and mac?
def test_2_track_reconstruction():

    partial_map = get_all_maps("test/scan")[1:3]

    sfm = SFM(partial_map)

    sfm.process()

    sfm.print_points()

    assert len(sfm.maps_3d) == 15
"""


def test_invalid_reconstruction_views():

    maps = get_all_maps("test/scan")

    invalid_maps = [maps[0], maps[4], maps[8]]  # no useful overlap

    sfm = SFM(invalid_maps)

    with pytest.raises(Exception) as e_info:
        sfm.process()

    assert str(e_info.value) == "Failed to reconstruct."
