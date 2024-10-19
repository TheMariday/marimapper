from multiprocessing import Process, Queue, Event
from marimapper.detector import (
    show_image,
    set_cam_default,
    Camera,
    TimeoutController,
    set_cam_dark,
    enable_and_find_led,
)
from marimapper.led import LED2D
from marimapper.utils import get_backend
from marimapper import logging


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
        self._detection_request = Queue()  # {led_id, view_id}
        self._detection_result = Queue()  # LED3D
        self._exit_event = Event()

        self._device = device
        self._dark_exposure = dark_exposure
        self._threshold = threshold
        self._led_backend_name = led_backend_name
        self._led_backend_server = led_backend_server
        self._display = display

    def detect(self, led_id: int, view_id: int):
        self._detection_request.put((led_id, view_id))

    def get_results(self) -> LED2D:
        return self._detection_result.get()

    def stop(self):
        self._exit_event.set()

    def run(self):

        led_backend = get_backend(self._led_backend_name, self._led_backend_server)

        cam = Camera(self._device)

        timeout_controller = TimeoutController()

        while not self._exit_event.is_set():

            if not self._detection_request.empty():
                set_cam_dark(cam, self._dark_exposure)
                led_id, view_id = self._detection_request.get()
                result = enable_and_find_led(
                    cam,
                    led_backend,
                    led_id,
                    view_id,
                    timeout_controller,
                    self._threshold,
                    self._display,
                )

                self._detection_result.put(result)
            else:
                set_cam_default(cam)
                if self._display:
                    image = cam.read()
                    show_image(image)

        logging.info("resetting cam!")
        set_cam_default(cam)
