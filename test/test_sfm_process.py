from marimapper.file_tools import get_all_2d_led_maps
from marimapper.sfm_process import SFM
from multiprocessing import Queue
import time


def test_sfm_process_basic():

    queue_2d = Queue()
    queue_3d = Queue()

    sfm_process = SFM(queue_2d, queue_3d)

    sfm_process.start()

    leds = get_all_2d_led_maps("scan")

    for led in leds:  # 2ms
        queue_2d.put(led)
    time.sleep(1)  # wait for all to be consumed
    leds_3d = queue_3d.get()  # 320ms
    assert len(leds_3d) == 21

    sfm_process.exit_event.set()


if __name__ == "__main__":
    test_sfm_process_basic()
