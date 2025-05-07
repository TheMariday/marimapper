from marimapper.sfm_process import SFM
from marimapper.file_tools import get_all_2d_led_maps
from marimapper.queues import Queue3D
from utils import get_test_dir
import time
import pytest

@pytest.mark.skip("This test is flakey, needs a re-write")
def test_sfm_process_basic():

    leds = get_all_2d_led_maps(get_test_dir("MariMapper-Test-Data/9_point_box"))

    sfm = SFM(existing_leds=leds, max_fill=0)

    output_queue = Queue3D()

    sfm.add_output_queue(output_queue)
    sfm.start()

    map_3d = output_queue.get(timeout=5)

    assert len(map_3d) == 21

    sfm.stop()
    timeout = time.time() + 5

    while sfm.is_alive():
        assert time.time() < timeout, "sfm has failed to stop"


def test_sfm_process_exit():

    leds = get_all_2d_led_maps(get_test_dir("MariMapper-Test-Data/9_point_box"))

    sfm = SFM(existing_leds=leds)

    output_queue = Queue3D()

    sfm.add_output_queue(output_queue)
    sfm.start()

    del sfm

    assert True
