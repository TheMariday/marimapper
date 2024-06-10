from parse import parse
import numpy as np
import os
import sys

sys.path.append("./")
from lib.utils import cprint, Col


class LEDMap3D:

    def __init__(self, data=None, filename=None):

        self.valid = True
        self.data = {}
        if data is not None:
            self.data = data
        if filename is not None:
            self.valid = self._load(filename)

    def __setitem__(self, led_index, led_data):
        self.data[led_index] = led_data

    def __getitem__(self, led_index):
        return self.data[led_index]

    def __contains__(self, led_index):
        return led_index in self.data

    def __len__(self):
        return len(self.data)

    def keys(self):
        return self.data.keys()

    def _load(self, filename):
        cprint(f"Reading 3D map {filename}...")

        if not os.path.exists(filename):
            cprint(
                f"Cannot read 2d map {filename} as file does not exist", format=Col.FAIL
            )
            return False

        with open(filename, "r") as f:
            lines = f.readlines()
            headings = lines[0].strip().split(",")

            if headings != ["index", "x", "y", "z", "xn", "yn", "zn", "error"]:
                cprint(
                    f"Cannot read 3d map {filename} as headings don't match",
                    format=Col.FAIL,
                )
                return False

            for i in range(1, len(lines)):

                line = lines[i].strip()

                values = parse(
                    "{index:^d},{x:^f},{y:^f},{z:^f},{xn:^f},{yn:^f},{zn:^f},{error:^f}",
                    line,
                )
                if values is not None:
                    pos = np.array(
                        [values.named["x"], values.named["y"], values.named["z"]]
                    )
                    normal = np.array(
                        [values.named["xn"], values.named["yn"], values.named["zn"]]
                    )
                    self.data[values.named["index"]] = {
                        "pos": pos,
                        "normal": normal,
                        "error": values.named["error"],
                    }
                else:
                    cprint(
                        f"Failed to read line {i} of {filename}: {line}",
                        format=Col.WARNING,
                    )
                    continue

        cprint(f"Read {len(self.data)} lines from 3D map {filename}...")
        return True

    def write_to_file(self, filename):
        cprint(
            f"Writing 3D map with {len(self.data)} leds to {filename}...",
            format=Col.BLUE,
        )

        lines = ["index,x,y,z,xn,yn,zn,error"]

        for led_id in sorted(self.data.keys()):
            lines.append(
                f"{led_id},"
                f"{self.data[led_id]['pos'][0]:f},"
                f"{self.data[led_id]['pos'][1]:f},"
                f"{self.data[led_id]['pos'][2]:f},"
                f"{self.data[led_id]['normal'][0]:f},"
                f"{self.data[led_id]['normal'][1]:f},"
                f"{self.data[led_id]['normal'][2]:f},"
                f"{self.data[led_id]['error']:f}"
            )

        with open(filename, "w") as f:
            f.write("\n".join(lines))
