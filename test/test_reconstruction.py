import sys

sys.path.append("./")

from lib.sfm.sfm import SFM


def test_reconstruction():

    sfm = SFM("test/scan")

    sfm.process()

    sfm.print_points()

    assert len(sfm.model.points) == 21
