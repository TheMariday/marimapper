import os
from parse import parse
from lib import logging


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
        self.valid = True
        if filepath:
            self.valid = self._load(filepath)

    def _load(self, filename):
        if not os.path.exists(filename):
            return False

        with open(filename, "r") as f:
            lines = f.readlines()

        headings = lines[0].strip().split(",")

        if headings != ["index", "u", "v"]:
            return False

        for i in range(1, len(lines)):

            line = lines[i].strip()

            values = parse("{index:^d},{u:^f},{v:^f}", line)
            if values is not None:
                self.add_detection(
                    values.named["index"],
                    LEDDetection(values.named["u"], values.named["v"]),
                )
            else:
                logging.error(f"Failed to read line {i} of {filename}: {line}")
                continue

        return True

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


def get_all_2d_led_maps(directory):
    led_maps_2d = []

    for filename in sorted(os.listdir(directory)):
        full_path = os.path.join(directory, filename)

        if not os.path.isfile(full_path):
            continue

        led_map_2d = LEDMap2D(full_path)
        if led_map_2d.valid:
            led_maps_2d.append(led_map_2d)

    return led_maps_2d
