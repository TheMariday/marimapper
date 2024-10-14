import argparse

from marimapper.detector import Detector
from marimapper.utils import add_camera_args
from marimapper import logging


def main():

    parser = argparse.ArgumentParser(
        description="Tests your webcam and LED detection algorithms"
    )

    add_camera_args(parser)

    args = parser.parse_args()

    if args.width * args.height < 0:
        logging.error(
            "Failed to start camera checker as both camera width and height need to be provided"
        )
        quit()

    detector = Detector(args.device, args.exposure, args.threshold, None)

    logging.info(
        "Camera connected! Hold an LED up to the camera to check LED identification"
    )
    detector.show_debug()  # this no longer works!


if __name__ == "__main__":
    main()
