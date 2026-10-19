from multiprocessing import get_logger, Process, Queue, Event
import time
from marimapper.camera import as_device_list, open_cameras
from marimapper.detector import (
    show_image,
    set_cam_default,
    Camera,
    TimeoutController,
    set_cam_dark,
    enable_and_find_led,
    enable_and_find_leds,
    find_leds,
    detector_window_name,
)
from marimapper.led import get_distance, get_color, LEDInfo
from marimapper.queues import (
    RequestDetectionsQueue,
    Queue2D,
    DetectionControlEnum,
    Queue3DInfo,
)
from functools import partial

logger = get_logger()


def backend_black(backend):
    buffer = [[0, 0, 0] for _ in range(backend.get_led_count())]
    try:
        backend.set_leds(buffer)
        return True
    except AttributeError:
        return False


def render_led_info(led_info: dict[int, LEDInfo], led_backend):
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
    cams: list[Camera],
    led_backend,
    view_ids: list[int],
    timeout_controller: TimeoutController,
    threshold: int,
    display: bool,
    output_queues: list[Queue2D],
):
    """
    Detects every led from led_id_from up to led_id_to in all cameras at once, each led
    being switched on only once. Returns the leds each camera found (one list per camera).
    Every camera is its own view, so every led gives one DETECT or SKIP per camera.
    """
    leds_per_camera: list[list] = [[] for _ in cams]

    for led_id in range(led_id_from, led_id_to):
        results = enable_and_find_leds(
            cams,
            led_backend,
            led_id,
            view_ids,
            timeout_controller,
            threshold,
            display,
        )

        for camera_leds, led in zip(leds_per_camera, results):
            for queue in output_queues:
                if led is not None:
                    queue.put(DetectionControlEnum.DETECT, led)
                else:
                    queue.put(DetectionControlEnum.SKIP, led_id)

            if led is not None:
                camera_leds.append(led)

    return leds_per_camera


class DetectorProcess(Process):

    def __init__(
        self,
        device,
        dark_exposure: int,
        threshold: int,
        backend_factory: partial,
        display: bool = True,
        check_movement=True,
    ):
        super().__init__()
        self._request_detections_queue = RequestDetectionsQueue()  # {led_id, view_id}
        self._output_queues: list[Queue2D] = []  # LED3D
        self._led_count: Queue = Queue()
        self._led_count.cancel_join_thread()
        self._input_3d_info_queue = Queue3DInfo()
        self._exit_event = Event()

        # one camera or several, every camera is its own view in the scan
        self._devices = as_device_list(device)
        self._dark_exposure = dark_exposure
        self._threshold = threshold
        self._led_backend_factory = backend_factory
        self._display = display
        self._check_movement = check_movement

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

    def put_in_all_output_queues(self, control: DetectionControlEnum, data):
        for queue in self._output_queues:
            queue.put(control, data)

    def run(self):

        led_backend = self._led_backend_factory()

        self._led_count.put(led_backend.get_led_count())

        cams = open_cameras(self._devices)
        camera_count = len(cams)

        timeout_controller = TimeoutController()

        # we quickly switch to dark mode here to throw any exceptions about the camera early
        for cam in cams:
            set_cam_dark(cam, self._dark_exposure)
            set_cam_default(cam)

        while not self._exit_event.is_set():

            if not self._request_detections_queue.empty():

                led_id_from, led_id_to, view_id = (
                    self._request_detections_queue.get_id_from_id_to_view()
                )

                # each camera is its own view, numbered one after the other from view_id
                view_ids = [view_id + index for index in range(camera_count)]

                success = backend_black(led_backend)
                if not success:
                    logger.debug("failed to blacken backend due to missing attribute")

                # scan start here
                for cam in cams:
                    set_cam_dark(cam, self._dark_exposure)

                # Firstly, if there are leds visible, break out
                if any(
                    point is not None
                    for point in find_leds(cams, self._threshold, self._display)
                ):
                    logger.error(
                        "Detector process can detect an LED when no LEDs should be visible"
                    )
                    for queue in self._output_queues:
                        queue.put(DetectionControlEnum.FAIL, None)
                    for cam in cams:
                        set_cam_default(cam)
                    continue

                leds_per_camera = detect_leds(
                    led_id_from,
                    led_id_to,
                    cams,
                    led_backend,
                    view_ids,
                    timeout_controller,
                    self._threshold,
                    self._display,
                    self._output_queues,
                )

                # every camera finishes its own view, either done or deleted
                for index, (cam, leds) in enumerate(zip(cams, leds_per_camera)):

                    camera_label = f"Camera {index + 1}: " if camera_count > 1 else ""

                    if len(leds) == 0:
                        logger.warning(f"{camera_label}no LEDs were detected")

                    movement = False
                    if self._check_movement and len(leds) > 0:
                        led_first = leds[0]

                        led_current = enable_and_find_led(
                            cam,
                            led_backend,
                            led_first.led_id,
                            view_ids[index],
                            timeout_controller,
                            self._threshold,
                            self._display,
                        )
                        if led_current is not None:
                            distance = get_distance(led_current, led_first)
                            if distance > 0.01:  # 1% movement
                                logger.error(
                                    f"{camera_label}Camera movement of {int(distance * 100)}% has been detected"
                                )
                                movement = True
                        else:
                            logger.warning(
                                f"{camera_label}Went back to check led {led_first.led_id} for movement, "
                                f"and led could no longer be found. Cannot perform movement check"
                            )  # this is failing unexpectedly, needs test
                            movement = False

                    for queue in self._output_queues:
                        queue.put(
                            (
                                DetectionControlEnum.DONE
                                if len(leds) > 0 and not movement
                                else DetectionControlEnum.DELETE
                            ),
                            view_ids[index],
                        )

                # and lets reset everything back to normal
                for cam in cams:
                    set_cam_default(cam)

            if self._request_detections_queue.empty():
                if self._display:
                    for index, cam in enumerate(cams):
                        show_image(
                            cam.read(), detector_window_name(index, camera_count)
                        )
                    time.sleep(1 / 60)

                if not self._input_3d_info_queue.empty():
                    led_info: dict[int, LEDInfo] = self._input_3d_info_queue.get()

                    success = render_led_info(led_info, led_backend)
                    if not success:
                        logger.debug(
                            "failed to update colourful backend buffer due to a missing attribute"
                        )

        logger.info("detector closing, resetting camera and backend")
        for cam in cams:
            set_cam_default(cam)
        backend_black(led_backend)
        time.sleep(1)  # wait a moment for the backend to update before closing
