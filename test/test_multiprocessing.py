from marimapper.sfm_process import SFM
from marimapper.file_tools import get_all_2d_led_maps
from marimapper.queues import Queue3D
from utils import get_test_dir


def test_sfm_process():

    leds = get_all_2d_led_maps(get_test_dir("MariMapper-Test-Data/can"))

    sfm = SFM(existing_leds=leds)

    output_queue = Queue3D()

    sfm.add_output_queue(output_queue)
    sfm.start()

    map_3d = output_queue.get(timeout=3)

    # interestingly, the led count here isn't deterministic...
    assert len(map_3d) > 0

    sfm.stop()


# We need more tests here for other multiprocess process
