import tempfile
from marimapper.led_map_2d import LEDMap2D, get_all_2d_led_maps


def test_partially_valid_data():
    temp_led_map_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    temp_led_map_file.write(
        b"""index,u,v
0,0.379490,0.407710
2,0,0
2.2,0,0
bananas,apples,grapes
"""
    )
    temp_led_map_file.close()

    led_map = LEDMap2D(filepath=temp_led_map_file.name)

    assert led_map.valid

    assert len(led_map) == 2

    assert led_map.get_detection(0).pos() == (0.379490, 0.407710)

    assert led_map.get_detection(2).pos() == (0, 0)


def test_invalid_path():

    led_map = LEDMap2D(filepath="doesnt-exist-i-hope")
    assert not led_map.valid


def test_get_all_maps():

    directory = tempfile.TemporaryDirectory()

    temp_led_map_file = tempfile.NamedTemporaryFile(
        delete=False, suffix=".csv", dir=directory.name
    )
    temp_led_map_file.write(
        b"""index,u,v
0,0.379490,0.407710
"""
    )
    temp_led_map_file.close()

    temp_led_map_file_invalid = tempfile.NamedTemporaryFile(
        delete=False, suffix=".html", dir=directory.name
    )
    temp_led_map_file_invalid.write(
        b"""index,u,v
0,0.379490,0.407710
"""
    )
    temp_led_map_file_invalid.close()

    all_maps = get_all_2d_led_maps(directory=directory.name)

    assert len(all_maps) == 1

    directory.cleanup()
