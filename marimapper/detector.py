import cv2
import time
import typing

from marimapper.camera import Camera
from marimapper.timeout_controller import TimeoutController
from marimapper.led import Point2D, LED2D

DETECTOR_WINDOW_NAME = "MariMapper - Detector"


def find_led_in_image(image: cv2.Mat, threshold: int = 128) -> typing.Optional[Point2D]:

    if len(image.shape) > 2:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    _, image_thresh = cv2.threshold(image, threshold, 255, cv2.THRESH_TOZERO)

    contours, _ = cv2.findContours(image_thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    led_response_count = len(contours)

    if led_response_count == 0:
        return None

    moments = cv2.moments(image_thresh)

    img_height = image.shape[0]
    img_width = image.shape[1]

    center_u = moments["m10"] / max(moments["m00"], 0.00001)
    center_v = moments["m01"] / max(moments["m00"], 0.00001)

    center_u = center_u / img_width
    v_offset = (img_width - img_height) / 2.0
    center_v = (center_v + v_offset) / img_width

    brightness = 1.0

    return Point2D(center_u, center_v, contours, brightness)  # todo, normalise contours


def draw_led_detections(image: cv2.Mat, led_detection: Point2D) -> cv2.Mat:

    render_image = (
        image if len(image.shape) == 3 else cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    )

    img_height = render_image.shape[0]
    img_width = render_image.shape[1]

    cv2.drawContours(
        render_image, led_detection.contours, -1, (255, 0, 0), 1
    )  # TODO, de-normalise contours once normalised

    u_abs = int(led_detection.u() * img_width)

    v_offset = (img_width - img_height) / 2.0

    v_abs = int(led_detection.v() * img_width - v_offset)

    cv2.drawMarker(
        render_image,
        (u_abs, v_abs),
        (0, 255, 0),
        markerSize=100,
    )

    return render_image


def show_image(image: cv2.Mat) -> None:
    cv2.imshow(DETECTOR_WINDOW_NAME, image)
    key = cv2.waitKey(1)

    if key == 27:  # esc
        raise KeyboardInterrupt


def set_cam_default(cam: Camera) -> None:
    if cam.state != "default":
        cam.reset()
        cam.eat()
        cam.state = "default"


def set_cam_dark(cam: Camera, exposure: int) -> None:
    if cam.state != "dark":
        cam.set_autofocus(0, 0)
        cam.set_exposure_mode(0)
        cam.set_gain(0)
        cam.set_exposure(exposure)
        cam.eat()
        cam.state = "dark"


def find_led(
    cam: Camera, threshold: int = 128, display: bool = True
) -> typing.Optional[Point2D]:

    image = cam.read()
    results = find_led_in_image(image, threshold)

    if display and results:
        rendered_image = draw_led_detections(image, results)
        show_image(rendered_image)

    return results


def enable_and_find_led(
    cam: Camera,
    led_backend,
    led_id: int,
    view_id: int,
    timeout_controller: TimeoutController,
    threshold: int,
    display: bool = False,
) -> LED2D:

    led = LED2D(led_id, view_id)

    if led_backend is None:
        return led

    # First wait for no leds to be visible
    while find_led(cam, threshold, display) is not None:
        pass

    # Set the led to on and start the clock
    response_time_start = time.time()

    led_backend.set_led(led_id, True)

    # Wait until either we have a result or we run out of time
    while (
        led.point is None and time.time() < response_time_start + timeout_controller.timeout
    ):
        led.point = find_led(cam, threshold, display)

    led_backend.set_led(led_id, False)

    if led.point is None:
        return led

    timeout_controller.add_response_time(time.time() - response_time_start)

    while find_led(cam, threshold, display) is not None:
        pass

    return led
