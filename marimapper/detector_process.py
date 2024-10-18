from multiprocessing import Process, Event, Queue
from marimapper.detector import (
    show_image,
    set_cam_default,
    Camera,
    TimeoutController,
    set_cam_dark,
    enable_and_find_led,
    DETECTOR_WINDOW_NAME,
)
from marimapper.utils import get_backend
import cv2


class DetectorProcess(Process):

    def __init__(
        self,
        device: str,
        dark_exposure: int,
        threshold: int,
        led_backend_name: str,
        led_backend_server: str,
        display: bool = True,
    ):
        super().__init__()

        self.exit_event = Event()
        self.detection_request = Queue()  # {led_id, view_id}
        self.detection_result = Queue()  # LED3D

        self._device = device
        self._dark_exposure = dark_exposure
        self._threshold = threshold
        self._led_backend_name = led_backend_name
        self._led_backend_server = led_backend_server
        self._display = display

    def __del__(self):
        self.close()

    def run(self):

        led_backend = get_backend(self._led_backend_name, self._led_backend_server)

        cam = Camera(self._device)

        timeout_controller = TimeoutController()

        while not self.exit_event.is_set():

            if not self.detection_request.empty():
                set_cam_dark(cam, self._dark_exposure)
                led_id, view_id = self.detection_request.get()
                result = enable_and_find_led(
                    cam,
                    led_backend,
                    led_id,
                    view_id,
                    timeout_controller,
                    self._threshold,
                )
                if result is not None:
                    self.detection_result.put(result)
            else:
                set_cam_default(cam)
                image = cam.read()
                show_image(image)

            # if we close the window
            if cv2.getWindowProperty(DETECTOR_WINDOW_NAME, cv2.WND_PROP_VISIBLE) <= 0:
                self.exit_event.set()
                continue

        cv2.destroyAllWindows()
        set_cam_default(cam)

    def shutdown(self):
        self.exit_event.set()
