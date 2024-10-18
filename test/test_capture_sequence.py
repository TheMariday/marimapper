import os
from marimapper.camera import Camera
from marimapper.detector import find_led
from marimapper.file_tools import write_2d_leds_to_file, load_detections
from marimapper.led import LED2D


def test_capture_sequence():
    output_dir_full = os.path.join(os.getcwd(), "test", "scan")

    os.makedirs(output_dir_full, exist_ok=True)

    for view_index in range(9):

        cam = Camera(
            f"MariMapper-Test-Data/9_point_box/cam_{view_index}/capture_%04d.png"
        )

        leds = []

        for led_id in range(24):

            point = find_led(cam, display=False)

            if point:
                leds.append(LED2D(led_id, 0, point))

        filepath = os.path.join(output_dir_full, f"led_map_2d_{view_index:04}.csv")

        write_2d_leds_to_file(leds, filepath)


def test_capture_sequence_correctness():
    for view_index in range(9):
        output_dir_full = os.path.join(os.getcwd(), "test", "scan")

        filepath = os.path.join(output_dir_full, f"led_map_2d_{view_index:04}.csv")

        leds = load_detections(filepath, view_index)

        if view_index in [0, 4, 8]:
            assert (  # If it's a straight on view, there should be 9 points
                len(leds) == 9
            )
        else:
            assert len(leds) == 15  # If it's a diagonal-ish view, then we see 15 points
