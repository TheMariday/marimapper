import shutil
import sys
from pathlib import Path

import pytest
from marimapper.file_tools import get_all_2d_led_maps
from marimapper.scripts.reconstruct_cli import main, reconstruct
from utils import get_test_dir


def test_reconstruct_does_what_the_scanner_does():
    maps = get_all_2d_led_maps(get_test_dir("scan"))

    leds_3d = reconstruct(maps)

    # the 21 leds that were seen, plus any short gaps the scanner interpolates after reconstructing
    assert 21 <= len(leds_3d) <= 25
    assert all(led.point.normal.any() for led in leds_3d)  # and the normals were added


def test_reconstruct_command_writes_the_3d_map(tmp_path, monkeypatch):
    for csv in Path(get_test_dir("scan")).glob("led_map_2d_*.csv"):
        shutil.copy(csv, tmp_path)

    monkeypatch.setattr(sys, "argv", ["marimapper_reconstruct", "--dir", str(tmp_path)])

    main()

    lines = Path(tmp_path, "led_map_3d.csv").read_text().strip().splitlines()
    assert lines[0] == "index,x,y,z,xn,yn,zn,error"
    assert 21 <= len(lines) - 1 <= 25


def test_reconstruct_command_needs_at_least_two_scans(tmp_path, monkeypatch):
    first = next(Path(get_test_dir("scan")).glob("led_map_2d_*.csv"))
    shutil.copy(first, tmp_path)

    monkeypatch.setattr(sys, "argv", ["marimapper_reconstruct", "--dir", str(tmp_path)])

    with pytest.raises(Exception, match="at least 2"):
        main()
