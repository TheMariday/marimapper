import tempfile
from marimapper.led_map_3d import LEDMap3D


def test_file_write():

    led_id = 0
    led_x = 0
    led_y = 0
    led_z = 0
    led_x_normal = 1
    led_y_normal = 1
    led_z_normal = 1
    led_error = 1

    led_dict = {
        "pos": (led_x, led_y, led_z),
        "normal": (led_x_normal, led_y_normal, led_z_normal),
        "error": led_error,
    }

    led_map = LEDMap3D({led_id: led_dict})

    assert led_map.keys() == [led_id]

    output_file = tempfile.NamedTemporaryFile(delete=False)

    led_map.write_to_file(output_file.name)

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
