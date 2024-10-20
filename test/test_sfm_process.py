from marimapper.file_tools import get_all_2d_led_maps
from marimapper.sfm_process import SFM


def test_sfm_process_basic():
    sfm_process = SFM()

    for led in get_all_2d_led_maps("scan"):
        sfm_process.add_detection(led)

    sfm_process.start()

    leds_3d = sfm_process.get_results()
    assert len(leds_3d) == 21

    sfm_process.stop()
