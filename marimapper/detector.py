import cv2
import time
import math
from multiprocessing import Process, Event, Queue

from marimapper.camera import Camera
from marimapper.timeout_controller import TimeoutController
from marimapper.led_map_2d import LEDDetection


def find_led_in_image(image, led_id=-1, threshold=128):

    if len(image.shape) > 2:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    _, image_thresh = cv2.threshold(image, threshold, 255, cv2.THRESH_TOZERO)

    contours, _ = cv2.findContours(image_thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    led_response_count = len(contours)
    if led_response_count == 0:
        return LEDDetection(valid=False)

    moments = cv2.moments(image_thresh)

    img_height = image.shape[0]
    img_width = image.shape[1]

    center_u = moments["m10"] / max(moments["m00"], 0.00001)
    center_v = moments["m01"] / max(moments["m00"], 0.00001)

    center_u = center_u / img_width
    v_offset = (img_width - img_height) / 2.0
    center_v = (center_v + v_offset) / img_width

    return LEDDetection(led_id, center_u, center_v, contours)


def draw_led_detections(image, results):

    render_image = (
        image if len(image.shape) == 3 else cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    )

    img_height = render_image.shape[0]
    img_width = render_image.shape[1]

    if results.valid:
        cv2.drawContours(render_image, results.contours, -1, (255, 0, 0), 1)

        u_abs = int(results.u * img_width)

        v_offset = (img_width - img_height) / 2.0

        v_abs = int(results.v * img_width - v_offset)

        cv2.drawMarker(
            render_image,
            (u_abs, v_abs),
            (0, 255, 0),
            markerSize=100,
        )

    return render_image


class Detector(Process):

    def __init__(self, device, dark_exposure, threshold, led_backend, display=True):
        super().__init__()

        self.exit_event = Event()
        self.detection_request = Queue()
        self.detection_result = Queue()

        self.device = device

        self.led_backend = led_backend
        self.display = display

        self.dark_exposure = dark_exposure

        self.threshold = threshold
        self.timeout_controller = TimeoutController()

        self.cam_state = "default"

    def __del__(self):
        self.close()

    @staticmethod
    def show_image(image):
        cv2.imshow("MariMapper", image)
        cv2.waitKey(1)

    def run(self):

        cam = Camera(self.device)

        while not self.exit_event.is_set():

            if not self.detection_request.empty():
                self.set_cam_dark(cam)
                led_id = self.detection_request.get()
                result = self.enable_and_find_led(led_id)
                if result is not None:
                    self.detection_result.put(result)
            else:
                self.set_cam_default(cam)
                image = cam.read()
                self.show_image(image)

            # if we close the window
            if cv2.getWindowProperty("MariMapper", cv2.WND_PROP_VISIBLE) <= 0:
                self.exit_event.set()
                continue

        cv2.destroyAllWindows()
        self.set_cam_default(cam)

    def shutdown(self):
        self.exit_event.set()

    def set_cam_default(self, cam):
        if self.cam_state != "default":
            cam.reset()
            cam.eat()
            self.cam_state = "default"

    def set_cam_dark(self, cam):
        if self.cam_state != "dark":
            cam.set_autofocus(0, 0)
            cam.set_exposure_mode(0)
            cam.set_gain(0)
            cam.set_exposure(self.dark_exposure)
            cam.eat()
            self.cam_state = "dark"

    def find_led(self, cam, led_id=-1):

        image = cam.read()
        results = find_led_in_image(image, led_id, self.threshold)

        if self.display:
            rendered_image = draw_led_detections(image, results)
            self.show_image(rendered_image)

        return results

    def enable_and_find_led(self, cam, led_id):

        if self.led_backend is None:
            return None

        # First wait for no leds to be visible
        while self.find_led(cam) is not None:
            pass

        # Set the led to on and start the clock
        response_time_start = time.time()

        if led_id != -1:
            self.led_backend.set_led(led_id, True)

        # Wait until either we have a result or we run out of time
        result = None
        while (
            result is None
            and time.time() < response_time_start + self.timeout_controller.timeout
        ):
            result = self.find_led(cam)

        self.led_backend.set_led(led_id, False)

        if result is None:
            return None

        self.timeout_controller.add_response_time(time.time() - response_time_start)

        while self.find_led(cam) is not None:
            pass

        return result

    def get_camera_motion(self, valid_leds, map_data_2d):

        if len(valid_leds) == 0:
            return 0

        for led_id in valid_leds:
            detection_new = self.enable_and_find_led(cam, led_id)
            if detection_new:
                detection_orig = map_data_2d.get_detection(led_id)

                distance_between_first_and_last = math.hypot(
                    detection_orig.u - detection_new.u,
                    detection_orig.v - detection_new.v,
                )
                return distance_between_first_and_last * 100

        return 100
