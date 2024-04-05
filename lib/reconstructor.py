import cv2

from lib.camera import Camera, CameraSettings
from lib.led_identifier import LedFinder
from lib.utils import cprint


class Reconstructor:

    def __init__(self, device, exposure, threshold, width=-1, height=-1, camera=None):
        cprint("Starting MariMapper...")

        self.settings_backup = None
        self.cam = Camera(device) if camera is None else camera
        self.settings_backup = CameraSettings(self.cam)

        self.width = width
        self.height = height
        self.exposure = exposure

        self.led_finder = LedFinder(threshold)

    def __enter__(self):

        if self.width != -1 or self.height != -1:
            self.cam.set_resolution(self.width, self.height)

        self.cam.set_autofocus(0, 0)
        self.cam.set_exposure_mode(0)
        self.cam.set_gain(0)
        self.cam.set_exposure(self.exposure)

        self.cam.ditch_frames(20)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.settings_backup is not None:
            cprint("Reverting camera changes...")
            self.settings_backup.apply(self.cam)
            cprint("Camera changes reverted")

    def show_debug(self):

        cv2.namedWindow("MariMapper", cv2.WINDOW_AUTOSIZE)

        while True:

            if cv2.getWindowProperty("MariMapper", cv2.WND_PROP_VISIBLE) <= 0:
                break

            self.find_led(debug=True)

    def find_led(self, debug=False):
        image = self.cam.read()
        results = self.led_finder.find_led(image)

        if debug:
            rendered_image = self.led_finder.draw_results(image, results)
            cv2.imshow("MariMapper", rendered_image)
            cv2.waitKey(1)

        return results
