import os

from lib.reconstructor import Reconstructor
from lib.led_map import LEDMap2D
from mock_camera import MockCamera


def test_capture_sequence():
    output_dir_full = os.path.join(os.getcwd(), "test", "scan")

    os.makedirs(output_dir_full, exist_ok=True)

    for view_index in range(9):

        mock_camera = MockCamera(device_id=view_index)

        reconstructor = Reconstructor(
            device=view_index,
            dark_exposure=-10,
            threshold=128,
            led_backend=None,
            width=mock_camera.get_width(),
            height=mock_camera.get_height(),
            camera=mock_camera,
        )

        led_map_2d = LEDMap2D()

        for led_id in range(24):

            result = reconstructor.find_led(False)

            if result:
                led_map_2d.add_detection(led_id, result)

        filepath = os.path.join(output_dir_full, f"capture_{view_index:04}.csv")

        led_map_2d.write_to_file(filepath)


def test_capture_sequence_correctness():
    for view_index in range(9):
        output_dir_full = os.path.join(os.getcwd(), "test", "scan")

        filepath = os.path.join(output_dir_full, f"capture_{view_index:04}.csv")

        led_map_2d = LEDMap2D(filepath)

        if view_index in [0, 4, 8]:
            assert (  # If it's a straight on view, there should be 9 points
                len(led_map_2d) == 9
            )
        else:
            assert (  # If it's a diagonal-ish view, then we see 15 points
                len(led_map_2d) == 15
            )
