import argparse
import sys
sys.path.append('./')
from lib.utils import AddCameraArgs
from lib import L3D
from lib.color_print import cprint, Col

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Tests your webcam and LED detection algorithms')

    AddCameraArgs(parser)

    args = parser.parse_args()

    if args.width * args.height < 0:
        cprint(f"Failed to start camera checker as both camera width and height need to be provided", format=Col.FAIL)
        quit()

    l3d = L3D.L3D(args.device, args.exposure, args.threshold, width=args.width, height=args.height)

    l3d.show_debug()
