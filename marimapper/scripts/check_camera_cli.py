import argparse

from marimapper.detector import find_led, set_cam_dark
from marimapper.utils import add_camera_args
from marimapper.camera import Camera
from marimapper import multiprocessing_logging as logging


def main():

    parser = argparse.ArgumentParser(
        description="Tests your webcam and LED detection algorithms"
    )

    add_camera_args(parser)

    args = parser.parse_args()

    cam = Camera(args.device)

    set_cam_dark(cam, args.exposure)

    logging.info(
        "Camera connected! Hold an LED up to the camera to check LED identification"
    )

    while True:
        find_led(cam, args.threshold)


if __name__ == "__main__":
    main()
