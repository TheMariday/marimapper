import logging
import argparse
import cv2
from lib.camera import Camera, CameraSettings
from lib.led_identifier import LedFinder

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
    parser.add_argument('--device', type=int, help='Camera device index', default=0)
    parser.add_argument('--width', type=int, help='Video width, uses camera default by default', default=-1)
    parser.add_argument('--height', type=int, help='Video height, uses camera default by default', default=-1)
    parser.add_argument('--exposure', type=int, help='Set exposure time, usually lower is shorter', default=-10)

    parser.add_argument('--threshold', type=int, help='Anything below this threshold will be disregarded', default=128)

    args = parser.parse_args()

    if args.width * args.height < 0:
        logging.critical(f"Failed to start camera checker as both camera width and height need to be provided")
        quit()

    update_resolution = args.width > 0 and args.height > 0

    cam = Camera(args.device)

    settings_backup = CameraSettings(cam)

    try:
        if update_resolution:
            cam.set_resolution(args.width, args.height)
        cam.set_autofocus(0, 0)
        cam.set_exposure_mode(0)
        cam.set_gain(0)
        cam.set_exposure(args.exposure)

        led_finder = LedFinder(args.threshold)

        while True:
            image = cam.read()
            results = led_finder.find_led(image)
            render_image = led_finder.draw_results(image, results)

            cv2.imshow('Webcam Feed - Press ESC to close this window', render_image)
            if cv2.waitKey(1) == 27:
                break  # esc to quit

    finally:
        logging.info("reverting camera changes")
        settings_backup.apply(cam)
