from lib.camera import Camera, CameraSettings
from lib.led_identifier import LedFinder
from lib.color_print import cprint
import cv2


class L3D:

    def __init__(self, device, exposure, threshold, width=-1, height=-1, camera=None):
        cprint("Starting L3D...")

        self.settings_backup = None
        self.cam = Camera(device) if camera is None else camera
        self.settings_backup = CameraSettings(self.cam)

        if width != -1 or height != -1:
            self.cam.set_resolution(width, height)

        self.cam.set_autofocus(0, 0)
        self.cam.set_exposure_mode(0)
        self.cam.set_gain(0)
        self.cam.set_exposure(exposure)

        self.cam.ditch_frames(20)

        self.led_finder = LedFinder(threshold)

    def __del__(self):
        if self.settings_backup is not None:
            cprint("Reverting camera changes...")
            self.settings_backup.apply(self.cam)
            cprint("Camera changes reverted")

    def show_debug(self):

        window_name = "LED Detection Debug"

        cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)

        while True:

            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) <= 0:
                break

            self.find_led(debug=True)

    def find_led(self, debug=False):
        image = self.cam.read()
        results = self.led_finder.find_led(image)

        if debug:
            rendered_image = self.led_finder.draw_results(image, results)
            cv2.imshow("LED Detection Debug", rendered_image)
            cv2.waitKey(1)

        return results
