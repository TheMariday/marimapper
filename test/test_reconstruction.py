import numpy as np

from lib.sfm.sfm import SFM
from lib.led_map_2d import get_all_2d_led_maps


def check_dimensions(map_3d, max_error):
    cube_sides = []
    cube_sides.append(map_3d[2]["pos"] - map_3d[0]["pos"])
    cube_sides.append(map_3d[4]["pos"] - map_3d[6]["pos"])
    cube_sides.append(map_3d[18]["pos"] - map_3d[16]["pos"])
    cube_sides.append(map_3d[20]["pos"] - map_3d[22]["pos"])

    cube_sides.append(map_3d[4]["pos"] - map_3d[2]["pos"])
    cube_sides.append(map_3d[20]["pos"] - map_3d[18]["pos"])
    cube_sides.append(map_3d[6]["pos"] - map_3d[0]["pos"])
    cube_sides.append(map_3d[22]["pos"] - map_3d[16]["pos"])

    cube_sides.append(map_3d[16]["pos"] - map_3d[0]["pos"])
    cube_sides.append(map_3d[18]["pos"] - map_3d[2]["pos"])
    cube_sides.append(map_3d[20]["pos"] - map_3d[4]["pos"])
    cube_sides.append(map_3d[22]["pos"] - map_3d[6]["pos"])

    cube_side_lengths = [np.linalg.norm(v) for v in cube_sides]

    cube_side_length_avg = np.average(cube_side_lengths)

    cube_side_deviation = [
        length / cube_side_length_avg for length in cube_side_lengths
    ]

    assert max(cube_side_deviation) < 1 + max_error
    assert min(cube_side_deviation) > 1 - max_error


def test_reconstruction():
    maps = get_all_2d_led_maps("test/scan")

    map_3d, cams = SFM.process(maps)

    assert len(map_3d) == 21

    check_dimensions(
        map_3d, max_error=0.01  # needs to have a max deviation of less than 1%
    )


def test_sparse_reconstruction():
    maps = get_all_2d_led_maps("test/scan")

    maps_sparse = [maps[1], maps[3], maps[5], maps[7]]

    map_3d, cams = SFM.process(maps_sparse)

    assert map_3d is not None

    assert len(map_3d) == 21

    check_dimensions(
        map_3d, max_error=0.03  # needs to have a max deviation of less than 3%
    )


def test_2_track_reconstruction():
    partial_map = get_all_2d_led_maps("test/scan")[1:3]

    map_3d, cams = SFM.process(partial_map)

    assert map_3d is not None

    assert len(map_3d) == 15


def test_invalid_reconstruction_views():
    maps = get_all_2d_led_maps("test/scan")

    invalid_maps = [maps[0], maps[4], maps[8]]  # no useful overlap

    map_3d, cams = SFM.process(invalid_maps)

    assert map_3d is None


def test_reconstruct_higbeam():
    highbeam_map = get_all_2d_led_maps("test/MariMapper-Test-Data/highbeam")

    map_3d, cams = SFM.process(highbeam_map)

    assert map_3d is not None
