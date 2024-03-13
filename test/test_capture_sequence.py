import sys

sys.path.append("./")
from lib import L3D
from lib import map_read_write
from mock_camera import MockCamera
import os


def test_capture_sequence():

    output_dir_full = os.path.join(os.getcwd(), "test", "scan")

    os.makedirs(output_dir_full, exist_ok=True)

    for view_index in range(9):

        mock_camera = MockCamera(device_id=view_index)

        l3d = L3D.L3D(
            device=view_index,
            exposure=0,
            threshold=128,
            width=mock_camera.get_width(),
            height=mock_camera.get_height(),
            camera=mock_camera,
        )

        map_data = []

        for led_id in range(24):

            result = l3d.find_led(False)

            if result:
                u, v = result.get_center_normalised()
                map_data.append({"index": led_id, "u": u, "v": v})

        filepath = os.path.join(output_dir_full, f"capture_{view_index}.csv")

        map_read_write.write_2d_map(filepath, map_data)


def test_capture_sequence_correctness():

    for view_index in range(9):
        output_dir_full = os.path.join(os.getcwd(), "test", "scan")

        filepath = os.path.join(output_dir_full, f"capture_{view_index}.csv")

        map_data = map_read_write.read_2d_map(filepath)

        print(map_data)

        if view_index in [0, 4, 8]:
            assert (  # If it's a straight on view, there should be 9 points
                len(map_data) == 9
            )
        else:
            assert (  # If it's a diagonal-ish view, then we see 15 points
                len(map_data) == 15
            )
