import os
from marimapper.led import Point2D, LED3D, LED2D
import typing
from pathlib import Path


def load_detections(filename: Path, view_id) -> typing.Optional[list[LED2D]]:

    if not os.path.exists(filename):
        return None

    if not filename.suffix == ".csv":
        return None

    with open(filename, "r") as f:
        lines = f.readlines()

    headings = lines[0].strip().split(",")

    if headings != ["index", "u", "v"]:
        return None

    leds = []

    for i in range(1, len(lines)):

        line = lines[i].strip().split(",")

        try:
            index = int(line[0])
            u = float(line[1])
            v = float(line[2])
        except (IndexError, ValueError):
            continue

        leds.append(LED2D(index, view_id, Point2D(u, v)))

    return leds


def get_all_2d_led_maps(directory: Path) -> list[LED2D]:
    points = []

    for view_id, filename in enumerate(sorted(os.listdir(directory))):
        full_path = Path(directory, filename)

        detections = load_detections(
            full_path, view_id
        )  # this is wrong < WHY DID I WRITE THIS???? IS IT NOT???

        if detections is not None:
            points.extend(detections)

    return points


def write_2d_leds_to_file(leds: list[LED2D], filename: Path):

    lines = ["index,u,v"]

    for led in sorted(leds, key=lambda led_t: led_t.led_id):
        lines.append(f"{led.led_id}," f"{led.point.u():f}," f"{led.point.v():f}")

    with open(filename, "w") as f:
        f.write("\n".join(lines))


def write_3d_leds_to_file(leds: list[LED3D], filename: Path):

    lines = ["index,x,y,z,xn,yn,zn,error"]

    for led in sorted(leds, key=lambda led_t: led_t.led_id):
        lines.append(
            f"{led.led_id},"
            f"{led.point.position[0]:f},"
            f"{led.point.position[1]:f},"
            f"{led.point.position[2]:f},"
            f"{led.point.normal[0]:f},"
            f"{led.point.normal[1]:f},"
            f"{led.point.normal[2]:f},"
            f"{led.point.error:f}"
        )

    with open(filename, "w") as f:
        f.write("\n".join(lines))
