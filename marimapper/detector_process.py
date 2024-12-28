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
from marimapper.detector_fast import detect_leds_fast
from marimapper.led import get_distance, get_color, LEDInfo
from marimapper.queues import (
    RequestDetectionsQueue,
    Queue2D,
    DetectionControlEnum,
    Queue3DInfo,
)
from marimapper.utils import get_backend, backend_black
import time

logger = get_logger()


def render_led_info(led_info: dict[int, int], led_backend):
    buffer = [[0, 0, 0] for _ in range(max(led_info.keys()) + 1)]
    for led_id in led_info:
        info = led_info[led_id]
        buffer[led_id] = [int(v / 10) for v in get_color(info)]

    try:
        led_backend.set_leds(buffer)
        return True
    except AttributeError:
        logger.debug(
            "tried to set a colourful backend buffer that doesn't have a set_leds method :("
        )
        return False


def detect_leds(
    led_id_from: int,
    led_id_to: int,
    cam: Camera,
    led_backend,
    view_id: int,
    timeout_controller: TimeoutController,
    threshold: int,
    display: bool,
    output_queues: list[Queue2D],
):
    leds = []
    for led_id in range(led_id_from, led_id_to):
        led = enable_and_find_led(
            cam,
            led_backend,
            led_id,
            view_id,
            timeout_controller,
            threshold,
            display,
        )

        for queue in output_queues:
            if led is not None:
                queue.put(DetectionControlEnum.DETECT, led)
                leds.append(led)
            else:
                queue.put(DetectionControlEnum.SKIP, led_id)
    return leds


class DetectorProcess(Process):

    def __init__(
        self,
        device: str,
        dark_exposure: int,
        threshold: int,
        led_backend_name: str,
        led_backend_server: str,
        display: bool = True,
        check_movement=True,
        fast=True,
    ):
        super().__init__()
        self._request_detections_queue = RequestDetectionsQueue()  # {led_id, view_id}
        self._output_queues: list[Queue2D] = []  # LED3D
        self._led_count: Queue = Queue()
        self._led_count.cancel_join_thread()
        self._input_3d_info_queue = Queue3DInfo()
        self._exit_event = Event()

        self._device = device
        self._dark_exposure = dark_exposure
        self._threshold = threshold
        self._led_backend_name = led_backend_name
        self._led_backend_server = led_backend_server
        self._display = display
        self._check_movement = check_movement
        self._fast = fast

    def get_input_3d_info_queue(self):
        return self._input_3d_info_queue

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

                led_id_from, led_id_to, view_id = (
                    self._request_detections_queue.get_id_from_id_to_view()
                )

                success = backend_black(led_backend)
                if not success:
                    logger.debug("failed to blacken backend due to missing attribute")

                # scan start here
                set_cam_dark(cam, self._dark_exposure)

                # Firstly, if there are leds visible, break out
                if find_led(cam, self._threshold, self._display) is not None:
                    logger.error(
                        "Detector process can detect an LED when no LEDs should be visible"
                    )
                    for queue in self._output_queues:
                        queue.put(DetectionControlEnum.FAIL, None)
                    set_cam_default(cam)
                    continue

                if self._fast:  # This is nasty but I'd prefer this than dynamic imports
                    leds = detect_leds_fast(
                        led_id_from,
                        led_id_to,
                        cam,
                        led_backend,
                        view_id,
                        timeout_controller,
                        self._threshold,
                        self._display,
                        self._output_queues,
                    )
                else:
                    leds = detect_leds(
                        led_id_from,
                        led_id_to,
                        cam,
                        led_backend,
                        view_id,
                        timeout_controller,
                        self._threshold,
                        self._display,
                        self._output_queues,
                    )

                if leds is not None and len(leds) > 0:

                    movement = False
                    if self._check_movement and not self._fast:
                        led_first = leds[0]

                        led_current = enable_and_find_led(
                            cam,
                            led_backend,
                            led_first.led_id,
                            view_id,
                            timeout_controller,
                            self._threshold,
                            self._display,
                        )
                        if led_current is not None:
                            distance = get_distance(led_current, led_first)
                            if distance > 0.01:  # 1% movement
                                movement = True
                        else:
                            logger.error(
                                f"went back to check led {led_first.led_id} for movement, and led could no longer be found"
                            )
                            movement = True

                    for queue in self._output_queues:
                        queue.put(
                            (
                                DetectionControlEnum.DONE
                                if not movement
                                else DetectionControlEnum.DELETE
                            ),
                            view_id,
                        )

                # and lets reset everything back to normal
                set_cam_default(cam)

            if self._request_detections_queue.empty():
                if self._display:
                    image = cam.read()
                    show_image(image)

                if not self._input_3d_info_queue.empty():
                    led_info: dict[int, LEDInfo] = self._input_3d_info_queue.get()

                    success = render_led_info(led_info, led_backend)
                    if not success:
                        logger.debug(
                            "failed to update colourful backend buffer due to a missing attribute"
                        )

        logger.info("detector closing, resetting camera and backend")
        set_cam_default(cam)
        backend_black(led_backend)
        time.sleep(1)  # wait a moment for the backend to update before closing
