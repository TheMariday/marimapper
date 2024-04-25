import numpy as np
import math


def _distance_between_leds(led_a, led_b):
    return math.hypot(*(led_a["pos"] - led_b["pos"]))


def _fill_gaps(led_map, start_led_id, end_led_id):

    missing_leds = end_led_id - start_led_id - 1

    for i in range(1, missing_leds + 1):
        led_map[start_led_id + i] = {}

        led_map[start_led_id + i]["pos"] = led_map[start_led_id]["pos"] + (
            led_map[end_led_id]["pos"] - led_map[start_led_id]["pos"]
        ) * (i / (missing_leds + 1))
        led_map[start_led_id + i]["error"] = led_map[start_led_id]["error"] + (
            led_map[end_led_id]["error"] - led_map[start_led_id]["error"]
        ) * (i / (missing_leds + 1))
        led_map[start_led_id + i]["normal"] = led_map[start_led_id]["normal"] + (
            led_map[end_led_id]["normal"] - led_map[start_led_id]["normal"]
        ) * (i / (missing_leds + 1))


def find_inter_led_distance(led_map):
    max_led_id = max(led_map.keys())

    distances = []

    for led_id in range(max_led_id):
        if led_id in led_map and led_id + 1 in led_map:
            dist = _distance_between_leds(led_map[led_id], led_map[led_id + 1])
            distances.append(dist)

    return np.median(distances)


def rescale(led_map, cameras=(), led_to_led_dist=1.0):

    scale = (1.0 / find_inter_led_distance(led_map)) * led_to_led_dist

    for led_id in led_map:
        led_map[led_id]["pos"] *= scale
        led_map[led_id]["normal"] *= scale
        led_map[led_id]["error"] *= scale

    for cam in cameras:
        cam[2] *= scale


def fill_gaps(led_map, max_dist_err=0.2, max_missing=5):

    total_leds_filled = 0

    led_to_led_distance = find_inter_led_distance(led_map)
    min_distance = (1 - max_dist_err) * led_to_led_distance
    max_distance = (1 + max_dist_err) * led_to_led_distance

    max_led_id = max(led_map.keys())
    min_led_id = min(led_map.keys())

    led_id = min_led_id
    while led_id < max_led_id:

        while led_id in led_map and led_id < max_led_id:
            led_id += 1

        # now we've hit a not-led
        start = led_id - 1
        while led_id not in led_map and led_id < max_led_id:
            led_id += 1

        end = led_id

        leds_missing = end - start - 1

        distance = _distance_between_leds(led_map[start], led_map[end])

        c = distance / (leds_missing + 1)

        if (min_distance < c < max_distance) and leds_missing < max_missing:
            _fill_gaps(led_map, start, end)
            total_leds_filled += leds_missing

    return total_leds_filled


def extract_strips(led_map, max_dist_err=0.5):

    max_led_id = max(led_map.keys())

    strips = [[]]
    led_id = -1

    led_to_led_distance = find_inter_led_distance(led_map)

    max_dist = (1 + max_dist_err) * led_to_led_distance
    min_dist = (1 - max_dist_err) * led_to_led_distance

    while True:

        led_id += 1

        if led_id > max_led_id:
            break

        if led_id not in led_map:
            continue

        if led_id + 1 not in led_map:
            if strips[-1]:
                strips[-1].append(led_id)
                strips.append([])
            continue

        distance = _distance_between_leds(led_map[led_id], led_map[led_id + 1])

        if not (min_dist < distance < max_dist):
            if strips[-1]:
                strips[-1].append(led_id)
                strips.append([])
            continue

        strips[-1].append(led_id)

    return strips
