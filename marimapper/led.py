import numpy as np
import typing
import math
from typing import Union

from multiprocessing import get_logger

logger = get_logger()


class View:
    def __init__(self, view_id, position, rotation):
        self.view_id = view_id
        self.rotation = rotation
        self.position = position


class Point2D:
    def __init__(self, u, v, contours=()):
        self.position: np.array = np.array([u, v])
        self.contours = contours

    def u(self):
        return self.position[0]

    def v(self):
        return self.position[1]


class LED2D:
    def __init__(
        self, led_id: int, view_id: int, point: typing.Optional[Point2D] = None
    ):
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


class LEDState:
    INTERPOLATED: int = 0
    MERGED: int = 1


class LED3D:

    def __init__(self, led_id):
        self.led_id = led_id
        self.point = Point3D()
        self.views: list[View] = []
        self.state = []

    def add_state(self, state: int):
        self.state.append(state)

    def has_state(self, state: int) -> bool:
        return state in self.state

    def get_color(self):
        if self.has_state(LEDState.INTERPOLATED):
            return 255, 0, 0
        if self.has_state(LEDState.MERGED):
            return 255, 0, 255

        return 0, 255, 0


# returns none if there isn't that led in the list!
def get_led(
    leds: list[Union[Union[LED2D, LED3D]]], led_id: int
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


def rescale(leds: list[LED3D], target_inter_distance=1.0) -> None:

    inter_led_distance = find_inter_led_distance(leds)
    scale = (1.0 / inter_led_distance) * target_inter_distance
    for led in leds:
        led.point *= scale
        for view in led.views:
            view.position = view.position * scale


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

        new_led.add_state(LEDState.INTERPOLATED)
        new_leds.append(new_led)

    return new_leds


def fill_gaps(leds: list[LED3D], max_distance: float = 1.1, max_missing=5):

    new_leds = []

    for led in leds:

        next_led = get_next(led, leds)

        if next_led is None:
            continue

        gap = get_gap(led, next_led) - 1

        if 1 <= gap <= max_missing:

            distance = get_distance(led, next_led)

            distance_per_led = distance / (gap + 1)

            if (distance_per_led < max_distance) and gap <= max_missing:
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
    new_led.add_state(LEDState.MERGED)

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
