import os.path

import numpy as np
from parse import parse

from lib.utils import cprint, Col


def read_2d_map(filename):
    cprint(f"Reading 2D map {filename}...")

    if not os.path.exists(filename):
        cprint(f"Cannot read 2d map {filename} as file does not exist", format=Col.FAIL)
        return None

    with open(filename, "r") as f:
        lines = f.readlines()

    headings = lines[0].strip().split(",")

    if headings != ["index", "u", "v"]:
        cprint(f"Cannot read 2d map {filename} as headings don't match index,u,v", format=Col.FAIL)
        return None

    data = {}

    for i in range(1, len(lines)):

        line = lines[i].strip()

        values = parse("{index:^d},{u:^f},{v:^f}", line)
        if values is not None:
            data[values.named["index"]] = {"pos": np.array([values.named["u"], values.named["v"]])}
        else:
            cprint(f"Failed to read line {i} of {filename}: {line}", format=Col.WARNING)
            continue

    cprint(f"Read {len(data)} lines from 2D map {filename}...")

    return data if data else None


def read_3d_map(filename):
    cprint(f"Reading 3D map {filename}...")

    if not os.path.exists(filename):
        cprint(f"Cannot read 2d map {filename} as file does not exist", format=Col.FAIL)
        return None

    data = {}

    with open(filename, "r") as f:
        lines = f.readlines()
        headings = lines[0].strip().split(",")

        if headings != ["index", "x", "y", "z", "error"]:
            cprint(f"Cannot read 2d map {filename} as headings don't match index,u,v", format=Col.FAIL)
            return None

        for i in range(1, len(lines)):

            line = lines[i].strip()

            values = parse("{index:^d},{x:^f},{y:^f},{z:^f},{error:^f}", line)
            if values is not None:
                pos = np.array([values.named["x"], values.named["y"], values.named["z"]])
                data[values.named["index"]] = {"pos": pos, "error": values.named["error"]}
            else:
                cprint(f"Failed to read line {i} of {filename}: {line}", format=Col.WARNING)
                continue

    cprint(f"Read {len(data)} lines from 3D map {filename}...")

    return data if data else None


def write_2d_map(filename, data):
    cprint(f"Writing 2D map to {filename}...")

    lines = ["index,u,v"]

    for led_id in data:
        lines.append(f"{led_id},"
                     f"{data[led_id]['pos'][0]:f},"
                     f"{data[led_id]['pos'][1]:f}")

    with open(filename, "w") as f:
        f.write("\n".join(lines))


def write_3d_map(filename, data):
    cprint(f"Writing 3D map to {filename}...")

    lines = ["index,x,y,z,error"]

    for led_id in data:
        lines.append(f"{led_id},"
                     f"{data[led_id]['pos'][0]:f},"
                     f"{data[led_id]['pos'][1]:f},"
                     f"{data[led_id]['pos'][2]:f},"
                     f"{data[led_id]['error']:f}")

    with open(filename, "w") as f:
        f.write("\n".join(lines))


def get_all_maps(directory):
    maps = []

    for filename in sorted(os.listdir(directory)):
        full_path = os.path.join(directory, filename)

        if not os.path.isfile(full_path):
            continue

        map = read_2d_map(full_path)
        if map is not None:
            maps.append(map)

    return maps
