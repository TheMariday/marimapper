import argparse

import sys

sys.path.append("./")
from lib.map_read_write import read_2d_map, read_3d_map
from lib.visualize_model import render_2d_model, render_3d_model

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Visualises 2D and 3D maps")

    parser.add_argument(
        "filename",
        type=str,
        help="The file to visualise, currently only supports 2D mapping",
    )

    args = parser.parse_args()

    map_data = read_2d_map(args.filename)

    if map_data:
        render_2d_model(map_data)
    else:
        map_data = read_3d_map(args.filename)
        if map_data:
            render_3d_model(map_data)
