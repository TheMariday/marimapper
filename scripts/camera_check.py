import logging
import argparse
import sys
sys.path.append('./')
from lib.utils import AddCameraArgs
from lib import L3D

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    print("""
    Welcome to Mariday's super-awesome camera checker!
    In a moment you should see a video feed from your webcam, don't worry it's supposed to be very dark!
    Turn on your phone flashlight and point it at the camera, you should be able to see a crosshair on the image!
    If your image is very dark, and the crosshair is in the right place, you're good to go!
    If the image is still too light, try either reducing the --exposure or increasing the --threshold
    """)

    parser = argparse.ArgumentParser(description='A tool to test whether your camera is compatible with L3D')

    AddCameraArgs(parser)

    args = parser.parse_args()

    if args.width * args.height < 0:
        logging.critical(f"Failed to start camera checker as both camera width and height need to be provided")
        quit()

    l3d = L3D.L3D(args.device, args.exposure, args.threshold, width=args.width, height=args.height)

    while l3d.show_debug():
        pass
