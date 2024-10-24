import argparse

from marimapper.detector import find_led, set_cam_dark
from marimapper.utils import add_camera_args
from marimapper.camera import Camera
from multiprocessing import log_to_stderr
import logging

logger = log_to_stderr()
logger.setLevel(level=logging.INFO)


def main():

    parser = argparse.ArgumentParser(
        description="Tests your webcam and LED detection algorithms"
    )

    add_camera_args(parser)
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    cam = Camera(args.device)

    set_cam_dark(cam, args.exposure)

    logger.info(
        "Camera connected! Hold an LED up to the camera to check LED identification"
    )

    while True:
        find_led(cam, args.threshold)


if __name__ == "__main__":
    main()
