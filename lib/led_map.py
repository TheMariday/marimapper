from lib.utils import cprint, Col
import os
from parse import parse

class LEDDetection:

    def __init__(self, u, v, contours=()):

        self.u = u
        self.v = v
        self.contours = contours

    def pos(self):
        return self.u, self.v


class LEDMap2D:

    def __init__(self, filepath=None):
        self._detections = {}
        if filepath:
            self._load(filepath)

    def _load(self, filename):
        cprint(f"Reading 2D map {filename}...")

        if not os.path.exists(filename):
            cprint(
                f"Cannot read 2d map {filename} as file does not exist", format=Col.FAIL
            )
            return None

        with open(filename, "r") as f:
            lines = f.readlines()

        headings = lines[0].strip().split(",")

        if headings != ["index", "u", "v"]:
            cprint(
                f"Cannot read 2d map {filename} as headings don't match index,u,v",
                format=Col.FAIL,
            )
            return None

        for i in range(1, len(lines)):

            line = lines[i].strip()

            values = parse("{index:^d},{u:^f},{v:^f}", line)
            if values is not None:
                self.add_detection(
                    values.named["index"],
                    LEDDetection(values.named["u"], values.named["v"]),
                )
            else:
                cprint(
                    f"Failed to read line {i} of {filename}: {line}", format=Col.WARNING
                )
                continue

        cprint(f"Read {len(self)} lines from 2D map {filename}...")

    def __len__(self):
        return len(self._detections)

    def led_indexes(self):
        return sorted(self._detections.keys())

    def get_detections(self):
        return self._detections

    def get_detection(self, led_id):
        return self._detections[led_id]

    def add_detection(self, led_id: int, detection: LEDDetection):
        self._detections[led_id] = detection

    def write_to_file(self, filename):

        lines = ["index,u,v"]

        for led_id in sorted(self.get_detections().keys()):
            detection = self.get_detection(led_id)
            lines.append(f"{led_id}," f"{detection.u:f}," f"{detection.v:f}")

        with open(filename, "w") as f:
            f.write("\n".join(lines))
