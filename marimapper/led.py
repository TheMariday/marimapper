import numpy as np
import typing
import math


class View:
    def __init__(self, view_id, position, rotation):
        self.view_id = view_id
        self.rotation = rotation
        self.position = position


class Point2D:
    def __init__(self, u, v, contours=(), brightness=1.0):
        self.position: np.array = np.array([u, v])
        self.contours = contours
        self.brightness: float = brightness

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

    def __add__(self, other):
        new = Point3D()
        new.position = self.position + other.position
        new.normal = self.normal + other.normal
        new.error = self.error + other.error
        return new

    def __sub__(self, other):
        new = Point3D()
        new.position = self.position - other.position
        new.normal = self.normal - other.normal
        new.error = self.error - other.error
        return new

    def __mul__(self, other):
        new = Point3D()
        new.position = self.position * other
        new.normal = self.normal * other
        new.error = self.error * other
        return new


class LED3D:
    def __init__(self, led_id):
        self.led_id = led_id
        self.point = Point3D()
        self.views: list[View] = []


# returns none if there isn't that led in the list!
def get_led(leds: list[LED2D | LED3D], led_id: int) -> typing.Optional[LED2D | LED3D]:
    for led in leds:
        if led.led_id == led_id:
            return led
    return None


def get_leds(leds: list[LED2D | LED3D], led_id: int) -> list[LED2D | LED3D]:
    return [led for led in leds if led.led_id == led_id]


# returns none if it's the end!
def get_next(
    led_prev: LED2D | LED3D, leds: list[LED2D | LED3D]
) -> typing.Optional[LED2D | LED3D]:

    closest = None
    for led in leds:

        if led.led_id > led_prev.led_id:

            if closest is None:
                closest = led
            else:
                if led.led_id - led_prev.led_id < closest.led_id - led_prev.led_id:
                    closest = led

    return closest


def get_gap(led_a: LED2D | LED3D, led_b: LED2D | LED3D) -> int:
    return abs(led_a.led_id - led_b.led_id)


def get_max_led_id(leds: list[LED2D | LED3D]) -> int:
    return max([led.led_id for led in leds])


def get_min_led_id(leds: list[LED2D | LED3D]) -> int:
    return min([led.led_id for led in leds])


def get_distance(led_a: LED2D | LED3D, led_b: LED2D | LED3D):
    return math.hypot(*(led_a.point.position - led_b.point.position))


def get_view_ids(leds: list[LED2D]) -> set[int]:
    return set([led.view_id for led in leds])


def get_leds_with_view(leds: list[LED2D], view_id: int) -> list[LED2D]:
    return [led for led in leds if led.view_id == view_id]


def last_view(leds: list[LED2D]):
    if len(leds) == 0:
        return -1
    return max([led.view_id for led in leds])


def find_inter_led_distance(leds: list[LED2D | LED3D]):
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
    print(inter_led_distance)
    scale = (1.0 / inter_led_distance) * target_inter_distance

    for led in leds:
        led.point *= scale


def recenter(leds: list[LED3D]):

    center = Point3D()

    center.position = np.median([led.point.position for led in leds], axis=0)
    print(f"center: {center.position}")
    for led in leds:
        led.point -= center


def fill_gap(start_led: LED3D, end_led: LED3D):

    total_missing_leds = end_led.led_id - start_led.led_id - 1

    new_leds = []
    for led_offset in range(1, total_missing_leds + 1):

        new_led = LED3D(start_led.led_id + led_offset)
        fraction = led_offset / (total_missing_leds + 1)

        new_led.position = start_led.point * (1 - fraction) + end_led.point * fraction

        new_leds.append(new_led)

    return new_leds


def fill_gaps(leds: list[LED3D], max_dist_err=0.2, max_missing=5) -> list[LED3D]:

    led_to_led_distance = find_inter_led_distance(leds)
    min_distance = (1 - max_dist_err) * led_to_led_distance
    max_distance = (1 + max_dist_err) * led_to_led_distance

    new_leds = []

    for led in leds:

        next_led = get_next(led, leds)
        gap = get_gap(led, next_led)
        if gap == 0:
            continue

        distance = get_distance(led, next_led)

        distance_per_led = distance / (gap + 1)

        if (min_distance < distance_per_led < max_distance) and gap < max_missing:
            new_leds += fill_gap(led, next_led)

    return new_leds


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

    return new_led


def remove_duplicates(leds: list[LED3D]) -> list[LED3D]:

    new_leds = []

    for led in leds:
        leds_found = get_leds(new_leds, led.led_id)
        if leds_found:
            new_leds.append(merge(leds_found))
        else:
            new_leds.append(led)

    return new_leds


def get_leds_with_views(leds: list[LED2D], view_ids) -> list[LED2D]:
    return [led for led in leds if led.view_id in view_ids]
