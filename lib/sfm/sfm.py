from pathlib import Path
from tempfile import TemporaryDirectory

import pycolmap
import sys

sys.path.append("./")

from lib.sfm.model import Model
from lib.sfm.visualize_model import render_model
from lib.sfm.database_populator import populate


class SFM:

    def __init__(self, input_directory):
        self.input_directory = input_directory
        self.database_directory = TemporaryDirectory()
        self.database_path = Path(self.database_directory.name) / "database.db"
        self.output_directory = TemporaryDirectory()

        self.model = None

    def process(self):

        max_led_index = populate(self.database_path, input_directory=Path(self.input_directory))

        im_folder = TemporaryDirectory()
        pycolmap.incremental_mapping(
            self.database_path, im_folder.name, self.output_directory.name
        )

        self.model = Model(Path(self.output_directory.name) / "0", max_led_index)

    def display(self):
        render_model(self.model)

    def print_points(self):

        for led_id in sorted(self.model.points.keys()):
            led = self.model.points[led_id]
            print(
                f"LED ID: {led_id}, LED Pos: {led['pos']}, LED Error: {led['error']}, Views: {led['views']}"
            )

    def save_points(self, filename):

        lines = ["x,y,z,error"]

        for led_id in sorted(self.model.points.keys()):
            led = self.model.points[led_id]
            lines.append(
                f"{led['pos'][0]}, {led['pos'][1]}, {led['pos'][2]}, {led['error']}"
            )

        with open(filename, "w") as f:
            f.write("\n".join(lines))
