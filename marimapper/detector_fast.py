from marimapper.camera import Camera
from marimapper.detector import show_image
from marimapper.led import LED2D, Point2D
from marimapper.timeout_controller import TimeoutController
from marimapper.queues import Queue2D
import logging
from multiprocessing import get_logger
import time
import cv2

from marimapper.utils import backend_black


logger = get_logger()


def get_binary_length(led_id: int) -> int:
    return len(bin(led_id)[2:])


def led_id_to_binary(led_id: int, binary_length: int) -> list[int]:

    binary_as_text = bin(led_id)[2:]
    binary_as_bool = [int(v) for v in binary_as_text]

    binary_padded = [0 for _ in range(binary_length)]

    binary_padded[-len(binary_as_bool) :] = binary_as_bool

    return binary_padded


def detect_leds_fast(
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

    # this isn't very smart if the led_id_from is non zero, oh well
    binary_length = get_binary_length(led_id_to)

    images = []

    # woah led0 is 0,0,0,0,0. nope
    led_binaries = [
        led_id_to_binary(led_id, binary_length) for led_id in range(led_id_to)
    ]

    for binary_index in range(binary_length):
        buffer = [
            [255, 255, 255] if led_binaries[led_id][binary_index] else [0, 0, 0]
            for led_id in range(led_id_to)
        ]
        led_backend.set_leds(buffer)
        # set backend
        cam.eat()
        image = cam.read()
        if display:
            show_image(image)

        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) / 255.0
        images.append(image)

    backend_black(backend)

    leds: list[LED2D] = []

    for led_id in range(1, led_id_to):
        mat = 1
        for binary_index in range(binary_length):
            if led_binaries[led_id][binary_index]:
                mat = images[binary_index] * mat
            else:
                mat = (1.0 - images[binary_index]) * mat

        _, mat_max, _, mat_max_loc = cv2.minMaxLoc(mat)
        min_response = min(
            [
                float(image[mat_max_loc[1], mat_max_loc[0]])
                for i, image in enumerate(images)
                if led_binaries[led_id][i]
            ]
        )

        if min_response > threshold / 255.0:
            point = Point2D(mat_max_loc[1], mat_max_loc[0])
            led = LED2D(led_id, view_id, point)
            leds.append(led)
            for queue in output_queues:
                queue.put(led)

    return leds


if __name__ == "__main__":

    from marimapper.backends.fcmega import fcmega_backend

    logger.setLevel(logging.DEBUG)

    cam = Camera(0)

    cam.set_exposure(-10)

    backend = fcmega_backend.Backend()

    timeout_controller = TimeoutController()

    leds = detect_leds_fast(0, 400, cam, backend, 0, timeout_controller, 128, True, [])

    for led in leds:
        print(led.point)

    time.sleep(1)
