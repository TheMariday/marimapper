import numpy as np
import math
from marimapper import logging


class LEDMap3D:

    def __init__(self, data=None):

        self.valid = True
        self.data = {}
        self.cameras = None
        if data is not None:
            self.data = data

    def __setitem__(self, led_index, led_data):
        self.data[led_index] = led_data

    def __getitem__(self, led_index):
        return self.data[led_index]

    def __contains__(self, led_index):
        return led_index in self.data

    def __len__(self):
        return len(self.data)

    def keys(self):
        return sorted(list(self.data.keys()))

    def get_connected_leds(self, max_ratio=1.5):
        connections = []

        inter_led_distance = self.get_inter_led_distance()

        led_ids = self.keys()

        for led_index in range(len(led_ids)):
            current_id = led_ids[led_index]
            next_id = led_ids[led_index] + 1
            if next_id in led_ids:
                if led_ids[led_index + 1] == next_id:

                    distance = math.hypot(
                        *(self[current_id]["pos"] - self[next_id]["pos"])
                    )
                    if distance < inter_led_distance * max_ratio:
                        connections.append((led_index, led_index + 1))

        return connections

    def rescale(self, target_inter_distance=1.0):

        scale = (1.0 / self.get_inter_led_distance()) * target_inter_distance

        for led_id in self.data:
            self[led_id]["pos"] *= scale
            self[led_id]["normal"] = self[led_id]["normal"] / np.linalg.norm(
                self[led_id]["normal"]
            )
            self[led_id]["normal"] *= target_inter_distance
            self[led_id]["error"] *= scale

        for cam in self.cameras:
            cam[1] *= scale

    def get_normal_list(self):
        return np.array([self[led_id]["normal"] for led_id in self.keys()])

    def get_inter_led_distance(self):
        max_led_id = max(self.keys())

        distances = []

        for led_id in range(max_led_id):
            if led_id in self.keys() and led_id + 1 in self.keys():
                dist = math.hypot(*(self[led_id]["pos"] - self[led_id + 1]["pos"]))
                distances.append(dist)

        return np.median(distances)

    def write_to_file(self, filename):
        logging.debug(f"Writing 3D map with {len(self.data)} leds to {filename}...")

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
