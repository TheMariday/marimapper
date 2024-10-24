import tempfile
import numpy as np
from marimapper.led import LED3D
from marimapper.file_tools import write_3d_leds_to_file
from pathlib import Path


def test_file_write():

    led_id = 0
    led_x = 0
    led_y = 0
    led_z = 0
    led_x_normal = 1
    led_y_normal = 1
    led_z_normal = 1
    led_error = 1

    led = LED3D(led_id)
    led.point.position = np.array([led_x, led_y, led_z])
    led.point.normal = np.array([led_x_normal, led_y_normal, led_z_normal])
    led.point.error = led_error

    output_file = tempfile.NamedTemporaryFile(delete=False)

    write_3d_leds_to_file([led], Path(output_file.name))

    with open(output_file.name) as f:
        lines = f.readlines()

        headings = ["index", "x", "y", "z", "xn", "yn", "zn", "error"]

        assert lines[0].strip().split(",") == headings
        data_line = lines[1].strip().split(",")
        assert int(data_line[headings.index("index")]) == led_id
        assert float(data_line[headings.index("x")]) == led_x
        assert float(data_line[headings.index("y")]) == led_y
        assert float(data_line[headings.index("z")]) == led_z
        assert float(data_line[headings.index("xn")]) == led_x_normal
        assert float(data_line[headings.index("yn")]) == led_y_normal
        assert float(data_line[headings.index("zn")]) == led_z_normal
        assert float(data_line[headings.index("error")]) == led_error
