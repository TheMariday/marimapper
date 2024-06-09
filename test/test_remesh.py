from lib.led_map_2d import get_all_2d_led_maps
from lib.sfm.sfm import SFM
from lib.remesher import remesh


def test_remesh_higbeam():
    highbeam_map = get_all_2d_led_maps("test/MariMapper-Test-Data/highbeam")

    sfm = SFM(highbeam_map)

    sfm.process()

    mesh_high_res = remesh(sfm.maps_3d, 8)

    assert 8000 < len(mesh_high_res.triangles) < 9000

    mesh_low_res = remesh(sfm.maps_3d, 4)

    assert 2000 < len(mesh_low_res.triangles) < 3000
