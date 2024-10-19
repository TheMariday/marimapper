from marimapper.file_tools import get_all_2d_led_maps
from marimapper.sfm_process import SFM
import time


def test_sfm_process_basic():

    sfm_process = SFM()

    sfm_process.start()

    leds = get_all_2d_led_maps("scan")

    for led in leds:  # 2ms
        sfm_process.add_detection(led)
    time.sleep(1)  # wait for all to be consumed
    leds_3d = sfm_process.get_results()
    assert len(leds_3d) == 21

    sfm_process.stop()


if __name__ == "__main__":
    test_sfm_process_basic()
