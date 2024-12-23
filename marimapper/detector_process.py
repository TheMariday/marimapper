from multiprocessing import get_logger, Process, Queue, Event
from marimapper.detector import (
    show_image,
    set_cam_default,
    Camera,
    TimeoutController,
    set_cam_dark,
    enable_and_find_led,
    find_led,
)

from marimapper.queues import RequestDetectionsQueue, Queue2D, DetectionControlEnum
from marimapper.utils import get_backend

logger = get_logger()


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
        self._request_detections_queue = RequestDetectionsQueue()  # {led_id, view_id}
        self._output_queues: list[Queue2D] = []  # LED3D
        self._led_count: Queue = Queue()
        self._led_count.cancel_join_thread()
        self._exit_event = Event()

        self._device = device
        self._dark_exposure = dark_exposure
        self._threshold = threshold
        self._led_backend_name = led_backend_name
        self._led_backend_server = led_backend_server
        self._display = display

    def get_request_detections_queue(self) -> RequestDetectionsQueue:
        return self._request_detections_queue

    def add_output_queue(self, queue: Queue2D):
        self._output_queues.append(queue)

    def detect(self, led_id_from: int, led_id_to: int, view_id: int):
        self._request_detections_queue.request(led_id_from, led_id_to, view_id)

    def get_led_count(self):
        return self._led_count.get()

    def stop(self):
        self._exit_event.set()

    def run(self):

        led_backend = get_backend(self._led_backend_name, self._led_backend_server)

        self._led_count.put(led_backend.get_led_count())

        cam = Camera(self._device)

        timeout_controller = TimeoutController()

        while not self._exit_event.is_set():

            if not self._request_detections_queue.empty():
                set_cam_dark(cam, self._dark_exposure)
                led_id_from, led_id_to, view_id = (
                    self._request_detections_queue.get_id_from_id_to_view()
                )

                # First wait for no leds to be visible
                if find_led(cam, self._threshold, self._display) is not None:
                    logger.error(
                        "Detector process can detect an LED when no LEDs should be visible"
                    )
                    for queue in self._output_queues:
                        queue.put(DetectionControlEnum.FAIL, None)

                else:

                    for led_id in range(led_id_from, led_id_to):
                        result = enable_and_find_led(
                            cam,
                            led_backend,
                            led_id,
                            view_id,
                            timeout_controller,
                            self._threshold,
                            self._display,
                        )

                        for queue in self._output_queues:
                            queue.put(DetectionControlEnum.DETECT, result)

                    movement = False  # TODO
                    if movement:
                        for queue in self._output_queues:
                            queue.put(DetectionControlEnum.DELETE, view_id)
                    else:
                        for queue in self._output_queues:
                            queue.put(DetectionControlEnum.DONE, view_id)

            else:
                set_cam_default(cam)
                if self._display:
                    image = cam.read()
                    show_image(image)

        logger.info("resetting cam!")
        set_cam_default(cam)
