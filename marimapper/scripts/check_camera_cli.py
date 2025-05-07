import argparse

import cv2

from marimapper.detector import find_led, set_cam_dark, find_led_in_image, show_image, draw_led_detections
from marimapper.scripts.arg_tools import (
    add_camera_args,
    add_common_args,
    parse_common_args,
)
from marimapper.camera import Camera
from multiprocessing import log_to_stderr
import logging

logger = log_to_stderr()
logger.setLevel(level=logging.INFO)


def main():

    parser = argparse.ArgumentParser(
        description="Tests your webcam and LED detection algorithms",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        usage=argparse.SUPPRESS,
    )

    add_common_args(parser)
    add_camera_args(parser)

    args = parser.parse_args()

    parse_common_args(args, logger)

    cam = Camera(args.device)

    set_cam_dark(cam, args.exposure)

    logger.info(
        "Camera connected! Hold an LED up to the camera to check LED identification"
    )
    import numpy as np
    image_last = cam.read()
    kernel = np.ones((3, 3), np.uint8)

    while True:

        image = cam.read()

        # image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        image_new = cv2.subtract(image, image_last)
        results = find_led_in_image(image_new, args.threshold)
        image_last = cv2.dilate( image.copy(), kernel)

        cv2.imshow("image_last", image_last)

        rendered_image = draw_led_detections(image_new, results)
        if results:
            cv2.imshow("image_new_results", rendered_image)
        else:
            cv2.imshow("image_new_no_results", rendered_image)

        cv2.waitKey(1)



if __name__ == "__main__":
    main()
