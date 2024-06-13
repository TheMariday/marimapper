import argparse
import sys

sys.path.append("./")

import numpy as np
import cv2
import colorsys
from lib.led_map_2d import LEDMap2D


def render_2d_model(led_map):
    display = np.ones((640, 640, 3)) * 0.2

    max_id = max(led_map.get_detections().keys())

    for led_id in led_map.get_detections():
        col = colorsys.hsv_to_rgb(led_id / max_id, 0.5, 1)
        pos = np.array(
            (led_map.get_detection(led_id).u, led_map.get_detection(led_id).v)
        )
        image_point = (pos * 640).astype(int)
        cv2.drawMarker(display, image_point, color=col)
        cv2.putText(
            display,
            str(led_id),
            image_point,
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            color=col,
        )

    cv2.imshow("MariMapper", display)
    cv2.waitKey(0)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Visualises 2D maps")

    parser.add_argument(
        "filename",
        type=str,
        help="The 2d_map file to visualise",
    )

    args = parser.parse_args()

    map_data = LEDMap2D(filepath=args.filename)

    render_2d_model(map_data)
