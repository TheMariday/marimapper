from copy import copy
import numpy as np
import typing
import math
from typing import Union
from enum import Enum
from multiprocessing import get_logger

logger = get_logger()


class View:
    def __init__(self, view_id, position, rotation):
        self.view_id = view_id
        self.rotation = rotation
        self.position = position


class Point2D:
    def __init__(self, u: float, v: float, contours=()):
        self.position: np.ndarray = np.array([u, v])
        self.contours = contours

    def u(self):
        return self.position[0]

    def v(self):
        return self.position[1]


class LED2D:
    def __init__(self, led_id: int, view_id: int, point: Point2D):
        self.led_id: int = led_id
        self.view_id: int = view_id
        self.point: Point2D = point


class Point3D:
    def __init__(self):
        self.position = np.zeros(3)
        self.normal = np.zeros(3)
        self.error = 0.0
        self.info = []

    def set_position(self, x, y, z):
        self.position = np.array([x, y, z])

    def __add__(self, other):
        new = Point3D()
        new.position = self.position + other.position
        new.normal = self.normal + other.normal
        new.error = self.error + other.error
        return new

    def __mul__(self, other):
        new = Point3D()
        new.position = self.position * other
        new.normal = self.normal * other
        new.error = self.error * other
        return new


class LEDInfo(Enum):
    NONE: int = 0

    RECONSTRUCTED: int = 1
    INTERPOLATED: int = 2
    MERGED: int = 3

    DETECTED: int = 4
    UNRECONSTRUCTABLE: int = 5


class Colors:
    RED = [255, 0, 0]
    GREEN = [0, 255, 0]
    BLUE = [0, 0, 255]
    ORANGE = [255, 165, 0]
    AQUA = [0, 255, 255]
    YELLOW = [255, 255, 0]
    PINK = [255, 0, 255]
    BLACK = [0, 0, 0]


def get_color(info: LEDInfo):

    if info == LEDInfo.RECONSTRUCTED:
        return Colors.GREEN
    if info in [LEDInfo.INTERPOLATED, LEDInfo.MERGED]:
        return Colors.AQUA
    if info == LEDInfo.DETECTED:
        return Colors.ORANGE
    if info == LEDInfo.UNRECONSTRUCTABLE:
        return Colors.RED

    return Colors.BLUE


class LED3D:

    def __init__(self, led_id: int):
        self.led_id: int = led_id
        self.point = Point3D()
        self.views: list[View] = []
        self.detections: list[LED2D] = []
        self.merged = False
        self.interpolated = False

    def has_position(self) -> bool:
        return bool(self.point.position.any())

    def get_info(self) -> LEDInfo:

        if self.interpolated:
            return LEDInfo.INTERPOLATED

        if self.merged:
            return LEDInfo.MERGED

        if self.has_position():
            return LEDInfo.RECONSTRUCTED

        if len(self.detections) >= 2:
            return LEDInfo.UNRECONSTRUCTABLE

        if len(self.detections) == 1:
            return LEDInfo.DETECTED

        return LEDInfo.NONE

    def get_color(self):
        info = self.get_info()
        return get_color(info)


# returns none if there isn't that led in the list!
def get_led(
    leds: list[Union[LED2D, LED3D]], led_id: int
) -> typing.Optional[Union[LED2D, LED3D]]:
    for led in leds:
        if led.led_id == led_id:
            return led
    return None


def get_leds(leds: list[Union[LED2D, LED3D]], led_id: int) -> list[Union[LED2D, LED3D]]:
    return [led for led in leds if led.led_id == led_id]


# returns none if it's the end!
def get_next(
    led_prev: Union[LED2D, LED3D], leds: list[Union[LED2D, LED3D]]
) -> typing.Optional[Union[LED2D, LED3D]]:

    closest = None
    for led in leds:

        if led.led_id > led_prev.led_id:

            if closest is None:
                closest = led
            else:
                if led.led_id - led_prev.led_id < closest.led_id - led_prev.led_id:
                    closest = led

    return closest


def get_gap(led_a: Union[LED2D, LED3D], led_b: Union[LED2D, LED3D]) -> int:
    return abs(led_a.led_id - led_b.led_id)


def get_distance(led_a: Union[LED2D, LED3D], led_b: Union[LED2D, LED3D]):
    return math.hypot(*(led_a.point.position - led_b.point.position))


def get_view_ids(leds: list[LED2D]) -> set[int]:
    return set([led.view_id for led in leds])


def get_leds_with_view(leds: list[LED2D], view_id: int) -> list[LED2D]:
    return [led for led in leds if led.view_id == view_id]


def last_view(leds: list[LED2D]):
    if len(leds) == 0:
        return -1
    return max([led.view_id for led in leds])


def find_inter_led_distance(leds: list[Union[LED2D, LED3D]]):
    distances = []

    for led in leds:
        next_led = get_next(led, leds)
        if next_led is not None:
            if get_gap(led, next_led) == 1:
                dist = get_distance(led, next_led)
                distances.append(dist)

    return np.median(distances)


def rescale(leds: list[LED3D], target_inter_distance=1.0) -> int:

    inter_led_distance = find_inter_led_distance(leds)
    scale = (1.0 / inter_led_distance) * target_inter_distance
    for led in leds:
        led.point *= scale
        for view in led.views:
            view.position = view.position * scale

    return scale


def recenter(leds: list[LED3D]):

    for led in leds:
        assert len(led.point.position) == 3

    center = np.median([led.point.position for led in leds], axis=0)
    for led in leds:
        led.point.position -= center
        for view in led.views:
            view.position = view.position - center


def fill_gap(start_led: LED3D, end_led: LED3D):

    total_missing_leds = end_led.led_id - start_led.led_id - 1

    new_leds = []
    for led_offset in range(1, total_missing_leds + 1):

        new_led = LED3D(start_led.led_id + led_offset)
        fraction = led_offset / (total_missing_leds + 1)
        p1 = start_led.point * (1 - fraction)
        p2 = end_led.point * fraction
        new_led.point = p1 + p2

        new_led.views = start_led.views + end_led.views

        new_led.interpolated = True
        new_leds.append(new_led)

    return new_leds


def fill_gaps(
    leds: list[LED3D],
    min_distance: float = 0.8,
    max_distance: float = 1.2,
    max_missing=5,
):

    new_leds = []

    for led in leds:

        next_led = get_next(led, leds)

        if next_led is None:
            continue

        gap = get_gap(led, next_led) - 1

        if 1 <= gap <= max_missing:

            distance = get_distance(led, next_led)

            distance_per_led = distance / (gap + 1)

            if (min_distance < distance_per_led < max_distance) and gap <= max_missing:
                new_leds += fill_gap(led, next_led)

    new_led_count = len(new_leds)

    if new_led_count > 0:
        logger.debug(f"filled {new_led_count} LEDs")

    leds += new_leds


def merge(leds: list[LED3D]) -> LED3D:

    # don't merge if it's a list of 1
    if len(leds) == 1:
        return leds[0]

    # ensure they all have the same ID
    assert all(led.led_id == leds[0].led_id for led in leds)

    new_led = LED3D(leds[0].led_id)

    new_led.views = [view for led in leds for view in led.views]

    new_led.point.position = np.average([led.point.position for led in leds], axis=0)
    new_led.point.normal = np.average([led.point.normal for led in leds], axis=0)
    new_led.point.error = sum([led.point.error for led in leds])
    new_led.merged = True
    return new_led


def remove_duplicates(leds: list[LED3D]) -> list[LED3D]:
    new_leds = []

    led_ids = set([led.led_id for led in leds])
    for led_id in led_ids:
        leds_found = get_leds(leds, led_id)
        if len(leds_found) == 1:
            new_leds.append(leds_found[0])
        else:
            new_leds.append(merge(leds_found))

    leds_merged = len(leds) - len(new_leds)
    if leds_merged > 0:
        logger.debug(f"merged {len(new_leds)} leds")

    return new_leds


def get_leds_with_views(leds: list[LED2D], view_ids) -> list[LED2D]:
    return [led for led in leds if led.view_id in view_ids]


def get_overlap_and_percentage(leds_2d, leds_3d, view) -> tuple[int, int]:

    if len(leds_2d) == 0 or len(leds_3d) == 0:
        return 0, 0

    leds_3d_ids = set([led.led_id for led in leds_3d])
    view_ids = [led.led_id for led in get_leds_with_view(leds_2d, view)]
    overlap_len = len(leds_3d_ids.intersection(view_ids))
    if len(view_ids) > 0:
        overlap_percentage = int((overlap_len / len(view_ids)) * 100)
    else:
        overlap_percentage = 0

    return overlap_len, overlap_percentage


def get_max_led_id(leds3d: list[LED3D]):
    return max([led.led_id for led in leds3d])


def combine_2d_3d(leds_2d: list[LED2D], leds_3d: list[LED3D]) -> list[LED3D]:

    new_leds_3d = copy(leds_3d)
    for led_2d in leds_2d:
        if led_2d.led_id not in [o.led_id for o in new_leds_3d]:
            new_leds_3d.append(LED3D(led_2d.led_id))

        for led in get_leds(new_leds_3d, led_2d.led_id):
            led.detections.append(led_2d)

    return new_leds_3d
