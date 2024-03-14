import argparse
import cv2
import numpy as np

import sys

sys.path.append("./")
from lib.map_read_write import read_2d_map, read_3d_map
from lib.sfm.visualize_model import render_model

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Visualises 2D and 3D maps")

    parser.add_argument(
        "filename",
        type=str,
        help="The file to visualise, currently only supports 2D mapping",
    )

    args = parser.parse_args()

    display = np.zeros((640, 640, 3))

    map_data = read_2d_map(args.filename)

    if map_data:

        for led_id in map_data:

            image_point = (map_data[led_id]["pos"] * 640).astype(int)
            cv2.drawMarker(display, image_point, color=(0, 255, 0))
            cv2.putText(
                display,
                str(led_id),
                image_point,
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                color=(0, 0, 255),
            )

        cv2.imshow("Visualise", display)
        cv2.waitKey(0)

    else:

        map_data = read_3d_map(args.filename)

        render_model(map_data, [])
