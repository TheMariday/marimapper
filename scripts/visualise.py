import argparse
import sys

sys.path.append("./")

from lib.visualize_model import render_2d_model, Renderer3D
from lib.led_map_2d import LEDMap2D


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Visualises 2D and 3D maps")

    parser.add_argument(
        "filename",
        type=str,
        help="The file to visualise, currently only supports 2D mapping",
    )

    args = parser.parse_args()

    map_data = LEDMap2D(filepath=args.filename)

    if map_data.valid:
        render_2d_model(map_data)
    else:
        r3d = Renderer3D(filename=args.filename)
        r3d.run()
