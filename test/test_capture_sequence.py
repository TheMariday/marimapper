import sys

sys.path.append("./")
from lib import L3D
from mock_camera import MockCamera
import os


def test_capture_sequence():

    output_dir_full = os.path.join(os.getcwd(), "my_scans", "test")

    os.makedirs(output_dir_full, exist_ok=True)

    for device_id in range(9):

        mock_camera = MockCamera(device_id=device_id)

        l3d = L3D.L3D(
            device_id,
            0,
            128,
            width=mock_camera.get_width(),
            height=mock_camera.get_height(),
            camera=mock_camera,
        )

        # The filename is made out of the date, then the resolution of the camera
        filename = (
            f"capture_cam_{device_id}_{l3d.cam.get_width()}_{l3d.cam.get_height()}.csv"
        )

        filepath = os.path.join(output_dir_full, filename)

        results_csv = []

        for led_id in range(24):

            result = l3d.find_led(False)

            if result:
                results_csv.append(f"{led_id},{result.center[0]},{result.center[1]}")

        with open(filepath, "w") as output_file:
            output_file.write("\n".join(results_csv))


def test_capture_sequence_correctness():

    mock_camera = MockCamera()

    for device_id in range(5):
        output_dir_full = os.path.join(os.getcwd(), "my_scans", "test")
        filename = f"capture_cam_{device_id}_{mock_camera.get_width()}_{mock_camera.get_height()}.csv"
        filepath = os.path.join(output_dir_full, filename)

        with open(filepath, "r") as csv_file:
            lines = csv_file.readlines()

            if device_id % 2:
                assert (  # If it's a diagonal view, then we will see 15 points
                    len(lines) == 15
                )
            else:
                assert (  # If it's a straight-on view, then we see 9 points
                    len(lines) == 9
                )

            for line in lines:
                led_id, u, v = line.split(",")
                int(led_id)
                float(u)
                float(v)
