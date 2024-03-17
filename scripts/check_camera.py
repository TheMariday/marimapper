import argparse
import sys

sys.path.append("./")

from lib import L3D
from lib.utils import add_camera_args, cprint, Col

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Tests your webcam and LED detection algorithms"
    )

    add_camera_args(parser)

    args = parser.parse_args()

    if args.width * args.height < 0:
        cprint(
            "Failed to start camera checker as both camera width and height need to be provided",
            format=Col.FAIL,
        )
        quit()

    with L3D.L3D(
        args.device, args.exposure, args.threshold, width=args.width, height=args.height
    ) as l3d:

        cprint(
            "Camera connected! Hold an LED up to the camera to check LED identification",
            format=Col.BLUE,
        )

        l3d.show_debug()
