import cv2
import time

from lib.camera import Camera, CameraSettings
from lib.led_identifier import LedFinder
from lib.utils import cprint
from lib.timeout_controller import TimeoutController


class Reconstructor:

    def __init__(
        self, device, exposure, threshold, led_backend, width=-1, height=-1, camera=None
    ):
        cprint("Starting MariMapper...")

        self.settings_backup = None
        self.cam = Camera(device) if camera is None else camera
        self.settings_backup = CameraSettings(self.cam)
        self.led_backend = led_backend

        self.exposure = exposure

        self.led_finder = LedFinder(threshold)
        self.timeout_controller = TimeoutController()

        if width != -1 and height != -1:
            self.cam.set_resolution(width, height)

        self.cam.set_autofocus(0, 0)
        self.cam.set_exposure_mode(0)
        self.cam.set_gain(0)
        self.cam.set_exposure(self.exposure)

        self.cam.ditch_frames(20)

    def __del__(self):
        if cv2.getWindowProperty("MariMapper", cv2.WND_PROP_VISIBLE) > 0:
            cv2.destroyWindow("MariMapper")

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

    def enable_and_find_led(self, led_id, debug=False):

        # First wait for no leds to be visible
        while self.find_led_in_camera() is not None:
            pass

        # Set the led to on and start the clock
        response_time_start = time.time()

        self.led_backend.set_led(led_id, True)

        # Wait until either we have a result or we run out of time
        result = None
        while (
            result is None
            and time.time() < response_time_start + self.timeout_controller.timeout
        ):
            result = self.find_led_in_camera(debug)

        self.led_backend.set_led(led_id, False)

        if result is None:
            return None

        self.timeout_controller.add_response_time(time.time() - response_time_start)

        while self.find_led_in_camera() is not None:
            pass

        return result
