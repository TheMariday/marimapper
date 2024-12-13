from marimapper.sfm_process import SFM
from marimapper.file_tools import get_all_2d_led_maps
from multiprocessing import Queue
from utils import get_test_dir


def test_sfm_process():

    sfm = SFM()

    leds = get_all_2d_led_maps(get_test_dir("MariMapper-Test-Data/can"))

    output_queue = Queue()

    for led in leds:
        sfm.add_detection(led)
    sfm.add_output_queue(output_queue)
    sfm.start()

    map_3d = output_queue.get(timeout=3)

    # interestingly, the led count here isn't deterministic...
    assert len(map_3d) > 0

    sfm.stop()


# We need more tests here for other multiprocess process
