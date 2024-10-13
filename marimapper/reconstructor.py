import cv2
import time
import math
from threading import Thread

from marimapper.camera import Camera, CameraSettings
from marimapper.led_identifier import find_led_in_image, draw_led_detections
from marimapper.timeout_controller import TimeoutController


class Reconstructor:

    def __init__(
        self,
        device,
        dark_exposure,
        threshold,
        led_backend,
        width=-1,
        height=-1,
    ):
        self.cam = Camera(device)
        self.settings_light = CameraSettings(self.cam)
        self.led_backend = led_backend

        self.dark_exposure = dark_exposure
        self.light_exposure = self.cam.get_exposure()

        self.threshold = threshold
        self.timeout_controller = TimeoutController()

        if width != -1 and height != -1:
            self.cam.set_resolution(width, height)

        self.cam.set_autofocus(0, 0)
        self.cam.set_exposure_mode(0)
        self.cam.set_gain(0)

        self.settings_dark = CameraSettings(self.cam)

        self.live_feed = None
        self.live_feed_running = False

    def __del__(self):
        self.close()

    def close(self):
        self.close_live_feed()
        cv2.destroyAllWindows()

        self.light()

    def light(self):
        self.settings_light.apply(self.cam)
        self.cam.eat()

    def dark(self):
        self.settings_dark.apply(self.cam)
        self.cam.eat()

    def open_live_feed(self):
        cv2.destroyAllWindows()
        self.live_feed_running = True
        self.live_feed = Thread(target=self._live_thread_loop)
        self.live_feed.start()

    def close_live_feed(self):
        self.live_feed_running = False
        if self.live_feed is not None:
            if self.live_feed.is_alive():
                self.live_feed.join()

    def _live_thread_loop(self):

        cv2.namedWindow("MariMapper", cv2.WINDOW_AUTOSIZE)

        while self.live_feed_running:

            if cv2.getWindowProperty("MariMapper", cv2.WND_PROP_VISIBLE) <= 0:
                self.live_feed_running = False

            image = self.cam.read(color=True)
            cv2.imshow("MariMapper", image)
            cv2.waitKey(1)

        cv2.destroyAllWindows()

    def show_debug(self):

        self.dark()

        cv2.namedWindow("MariMapper", cv2.WINDOW_AUTOSIZE)

        while True:

            if cv2.getWindowProperty("MariMapper", cv2.WND_PROP_VISIBLE) <= 0:
                break

            self.find_led(debug=True)

    def find_led(self, debug=False):

        image = self.cam.read()
        results = find_led_in_image(image, self.threshold)

        if debug:
            rendered_image = draw_led_detections(image, results)
            cv2.imshow("MariMapper", rendered_image)
            cv2.waitKey(1)

        return results

    def enable_and_find_led(self, led_id, debug=False):

        if self.led_backend is None:
            return None

        # First wait for no leds to be visible
        while self.find_led(debug) is not None:
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
            result = self.find_led(debug)

        self.led_backend.set_led(led_id, False)

        if result is None:
            return None

        self.timeout_controller.add_response_time(time.time() - response_time_start)

        while self.find_led(debug) is not None:
            pass

        return result

    def get_camera_motion(self, valid_leds, map_data_2d):

        if len(valid_leds) == 0:
            return 0

        for led_id in valid_leds:
            detection_new = self.enable_and_find_led(led_id, debug=True)
            if detection_new:
                detection_orig = map_data_2d.get_detection(led_id)

                distance_between_first_and_last = math.hypot(
                    detection_orig.u - detection_new.u,
                    detection_orig.v - detection_new.v,
                )
                return distance_between_first_and_last * 100

        return 100
