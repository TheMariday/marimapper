from lib.camera import Camera, CameraSettings
from lib.led_identifier import LedFinder, LedResults
import logging
import cv2


class L3D:

    def __init__(self, device, exposure, threshold, width=-1, height=-1):
        self.cam = Camera(device)

        self.settings_backup = CameraSettings(self.cam)

        if width != -1 or height != -1:
            self.cam.set_resolution(width, height)

        self.cam.set_autofocus(0, 0)
        self.cam.set_exposure_mode(0)
        self.cam.set_gain(0)
        self.cam.set_exposure(exposure)

        self.ditch_frames(20)

        self.led_finder = LedFinder(threshold)

    def __del__(self):
        logging.info("reverting camera changes")
        self.settings_backup.apply(self.cam)

    def show_debug(self):

        image = self.cam.read()
        results = self.led_finder.find_led(image)
        render_image = self.led_finder.draw_results(image, results)

        cv2.imshow('Webcam Feed - Press ESC to close this window', render_image)
        return cv2.waitKey(1) != 27

    def ditch_frames(self, count=20):
        for _ in range(count):
            self.cam.read()

    def find_led(self, debug=False):
        image = self.cam.read()
        results = self.led_finder.find_led(image)

        if debug:
            rendered_image = self.led_finder.draw_results(image, results)
            cv2.imshow('Webcam Feed - Press ESC to close this window', rendered_image)
            cv2.waitKey(1)

        return results
