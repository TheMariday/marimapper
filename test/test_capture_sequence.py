import os

from marimapper.reconstructor import Reconstructor
from marimapper.led_map_2d import LEDMap2D


def test_capture_sequence():
    output_dir_full = os.path.join(os.getcwd(), "test", "scan")

    os.makedirs(output_dir_full, exist_ok=True)

    for view_index in range(9):

        reconstructor = Reconstructor(
            device=f"test/MariMapper-Test-Data/9_point_box/cam_{view_index}/capture_%04d.png",
            dark_exposure=-10,
            threshold=128,
            led_backend=None,
        )

        led_map_2d = LEDMap2D()

        for led_id in range(24):

            result = reconstructor.find_led(False)

            if result:
                led_map_2d.add_detection(led_id, result)

        filepath = os.path.join(output_dir_full, f"led_map_2d_{view_index:04}.csv")

        led_map_2d.write_to_file(filepath)


def test_capture_sequence_correctness():
    for view_index in range(9):
        output_dir_full = os.path.join(os.getcwd(), "test", "scan")

        filepath = os.path.join(output_dir_full, f"led_map_2d_{view_index:04}.csv")

        led_map_2d = LEDMap2D(filepath)

        if view_index in [0, 4, 8]:
            assert (  # If it's a straight on view, there should be 9 points
                len(led_map_2d) == 9
            )
        else:
            assert (  # If it's a diagonal-ish view, then we see 15 points
                len(led_map_2d) == 15
            )
