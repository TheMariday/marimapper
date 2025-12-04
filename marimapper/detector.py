import logging

import cv2
import time
from typing import Optional
import numpy as np
from multiprocessing import get_logger

from marimapper.camera import Camera
from marimapper.timeout_controller import TimeoutController
from marimapper.led import Point2D, LED2D
from marimapper.window_state import apply_window_state, register_on_exit_capture


logger = get_logger()
_window_created = False
_state_applied = False


def contour_brightness(image: np.ndarray, contour: np.ndarray) -> int:
    """Calculate the sum of all pixels within a contour."""
    mask = np.zeros(image.shape, dtype=np.uint8)
    cv2.drawContours(mask, [contour], -1, 255, -1)
    masked_image = cv2.bitwise_and(image, image, mask=mask)
    return cv2.sumElems(masked_image)


def find_led_in_image(image: np.ndarray, threshold: int = 128) -> Optional[Point2D]:

    if len(image.shape) > 2:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    _, image_thresh = cv2.threshold(image, threshold, 255, cv2.THRESH_TOZERO)

    contours, _ = cv2.findContours(image_thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) == 0:
        return None

    brightest_contour = sorted(
        contours, key=lambda c: contour_brightness(image, c), reverse=True
    )[0]

    moments = cv2.moments(brightest_contour)

    center_u = moments["m10"] / max(moments["m00"], 0.00001)
    center_v = moments["m01"] / max(moments["m00"], 0.00001)

    # I am not sure why this is the case but sometimes is
    # Am I going to find out why, no, no I am not
    if center_u == 0 or center_v == 0:
        return None

    img_height, img_width = image.shape

    center_u = center_u / img_width
    v_offset = (img_width - img_height) / 2.0
    center_v = (center_v + v_offset) / img_width

    return Point2D(center_u, center_v, contours)  # todo, normalise contours


def draw_led_detections(image: cv2.Mat, led_detection: Optional[Point2D]) -> np.ndarray:
    render_image = (
        image if len(image.shape) == 3 else cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    )

    if led_detection is None:
        return render_image

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


def show_image(image: np.ndarray) -> None:
    global _window_created, _state_applied

    window_name = "MariMapper - Detector"

    # First call: create resizable window
    if not _window_created:
        logger.debug(f"First call to show_image, creating resizable window...")
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        _window_created = True
        register_on_exit_capture(window_name)

    cv2.imshow(window_name, image)

    # Apply saved state after first imshow (window must exist for resize/move to work)
    if not _state_applied:
        logger.debug(f"Applying saved window state...")
        apply_window_state(window_name)
        _state_applied = True

    key = cv2.waitKey(1)

    if key == 27:  # esc
        raise KeyboardInterrupt


def set_cam_default(cam: Camera) -> None:

    logger.info("resetting cam to default")
    cam.reset()
    cam.eat()


def set_cam_dark(cam: Camera, exposure: int) -> bool:
    logger.info("setting cam to dark mode")
    cam.set_autofocus(0, 0)
    cam.set_exposure_mode(0)
    cam.set_gain(0)
    if not cam.set_exposure(exposure):
        logger.warning(
            f"failed to set exposure to {exposure}, your camera might not support exposure control, "
            f"try darkening the scene and adjusting the threshold with --threshold "
        )

    exposure_success = cam.set_exposure(exposure)
    cam.eat()

    return exposure_success


def find_led(
    cam: Camera, threshold: int = 128, display: bool = True
) -> Optional[Point2D]:

    image = cam.read()
    results = find_led_in_image(image, threshold)

    if display:
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
) -> Optional[LED2D]:

    darkness_timeout_seconds = 3.0

    # First wait for no leds to be visible, this should always be false
    start = time.time()
    while find_led(cam, threshold, display) is not None:
        if time.time() - start > darkness_timeout_seconds:
            logging.warning(
                f"Detector can't start detecting led {led_id} as an led is already visible"
            )
            return None

    # Set the led to on and start the clock
    response_time_start = time.time()

    led_backend.set_led(led_id, True)

    # Wait until either we have a result or we run out of time
    point = None
    while (
        point is None and time.time() < response_time_start + timeout_controller.timeout
    ):
        point = find_led(cam, threshold, display)

    led_backend.set_led(led_id, False)

    if point is None:
        return None

    timeout_controller.add_response_time(time.time() - response_time_start)

    start = time.time()
    while find_led(cam, threshold, display) is not None:
        if time.time() - start > darkness_timeout_seconds:
            logging.warning(
                f"Detector can't stop detecting led {led_id} as an led is already visible, retrying backend..."
            )
            led_backend.set_led(led_id, False)
            start = time.time()

    return LED2D(led_id, view_id, point)
