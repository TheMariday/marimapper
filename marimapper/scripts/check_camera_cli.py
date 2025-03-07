import argparse

from marimapper.detector import find_led, set_cam_dark
from marimapper.utils import add_common_args, get_marimapper_version
from marimapper.camera import Camera
from multiprocessing import log_to_stderr
import logging

logger = log_to_stderr()
logger.setLevel(level=logging.INFO)


def main():

    parser = argparse.ArgumentParser(
        description="Tests your webcam and LED detection algorithms",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    add_common_args(parser)

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if args.version:
        print(f"Marimapper camera checker, version {get_marimapper_version()}")
        quit()

    cam = Camera(args.device)

    set_cam_dark(cam, args.exposure)

    logger.info(
        "Camera connected! Hold an LED up to the camera to check LED identification"
    )

    while True:
        find_led(cam, args.threshold)


if __name__ == "__main__":
    main()
