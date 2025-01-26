import tempfile
from pathlib import Path
from marimapper.file_tools import load_detections, get_all_2d_led_maps
from marimapper.led import get_led


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

    led_map = load_detections(Path(temp_led_map_file.name), 0)

    assert led_map is not None

    assert len(led_map) == 2

    assert get_led(led_map, 0).point.position[0] == 0.379490
    assert get_led(led_map, 0).point.position[1] == 0.407710
    assert get_led(led_map, 2).point.position[0] == 0
    assert get_led(led_map, 2).point.position[1] == 0

def test_missing_headers():
    temp_led_map_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    temp_led_map_file.write(
        b"""index,v,u
0,0.379490,0.407710"""
)

    temp_led_map_file.close()

    led_map = load_detections(Path(temp_led_map_file.name), 0)

    assert led_map is None, "led map successfully loaded without correct headers"


def test_invalid_path():

    led_map = load_detections(Path("doesnt-exist-i-hope"), 0)
    assert led_map is None, "led map successfully loaded from invalid file"


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

    all_maps = get_all_2d_led_maps(Path(directory.name))

    assert len(all_maps) == 1, 'expected 1 map'

    directory.cleanup()
