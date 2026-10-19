import argparse

from marimapper.detector import find_leds, set_cam_dark
from marimapper.scripts.arg_tools import (
    add_camera_args,
    add_common_args,
    parse_common_args,
)
from marimapper.camera import open_cameras
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

    cams = open_cameras(args.device)

    for cam in cams:
        set_cam_dark(cam, args.exposure)

    logger.info(
        "Camera connected! Hold an LED up to the camera to check LED identification"
        if len(cams) == 1
        else f"{len(cams)} cameras connected! Hold an LED up to each camera to check LED identification"
    )

    while True:
        find_leds(cams, args.threshold)


if __name__ == "__main__":
    main()
