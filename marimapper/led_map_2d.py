import os
from marimapper import logging


class LEDDetection:

    def __init__(self, led_id=-1, u=0.0, v=0.0, contours=(), valid=True):
        self.led_id = led_id
        self.u = u
        self.v = v
        self.contours = contours
        self.valid = valid

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

        if not filename.endswith(".csv"):
            return False

        with open(filename, "r") as f:
            lines = f.readlines()

        headings = lines[0].strip().split(",")

        if headings != ["index", "u", "v"]:
            return False

        for i in range(1, len(lines)):

            line = lines[i].strip().split(",")

            try:
                index = int(line[0])
                u = float(line[1])
                v = float(line[2])
            except (IndexError, ValueError):
                logging.warn(f"Failed to read line {i} of {filename}: {line}")
                continue

            self.add_detection(LEDDetection(index, u, v))

        return True

    def __len__(self):
        return len(self._detections)

    def led_indexes(self):
        return sorted(self._detections.keys())

    def get_detections(self):
        return self._detections

    def get_detection(self, led_id):
        return self._detections[led_id]

    def add_detection(self, detection: LEDDetection):
        if detection.valid:
            self._detections[detection.led_id] = detection

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

        led_map_2d = LEDMap2D(full_path)
        if led_map_2d.valid:
            led_maps_2d.append(led_map_2d)

    return led_maps_2d
