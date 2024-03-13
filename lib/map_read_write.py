import os.path
from parse import parse
import sys
sys.path.append("./")
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

    data = []

    for i in range(1, len(lines)):

        line = lines[i].strip()

        values = parse("{index:^d},{u:^f},{v:^f}", line)
        if values is not None:
            data.append(values.named)
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

    data = []

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
                data.append(values.named)
            else:
                cprint(f"Failed to read line {i} of {filename}: {line}", format=Col.WARNING)
                continue

    cprint(f"Read {len(data)} lines from 3D map {filename}...")

    return data if data else None


def _write_map(filename, data, keys):

    lines = [",".join(keys)]

    for i in range(len(data)):
        row = [str(data[i][v]) for v in keys]
        lines.append(",".join(row))

    with open(filename, "w") as f:
        f.write("\n".join(lines))


def write_2d_map(filename, data):

    cprint(f"Writing 2D map to {filename}...")

    _write_map(filename, data, ["index", "u", "v"])


def write_3d_map(filename, data):

    cprint(f"Writing 3D map to {filename}...")

    _write_map(filename, data, ["index", "x", "y", "z", "error"])


def get_all_maps(directory):
    maps = []

    for filename in sorted(os.listdir(directory)):
        map = read_2d_map(os.path.join(directory, filename))
        if map is not None:
            maps.append(map)

    if maps:
        cprint(f"Loaded {len(maps)} maps from {directory}")
    else:
        cprint(f"Failed to load any maps from {directory}", format=Col.FAIL)

    return maps
