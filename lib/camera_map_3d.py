from parse import parse
import os
import sys

sys.path.append("./")
from lib.utils import cprint, Col

class CameraMap3D:

    def __init__(self, filename=None):

        self.valid = True
        self.cameras = {}
        if filename is not None:
            self.valid = self._load(filename)

    def _load(self, filename):
        cprint(f"Reading camera map {filename}...")

        if not os.path.exists(filename):
            cprint(
                f"Cannot read camera map {filename} as file does not exist", format=Col.FAIL
            )
            return False

        with open(filename, "r") as f:
            lines = f.readlines()
            headings = lines[0].strip().split(",")

            if headings != ["camera_id", "x", "y", "z", "rw", "rx", "ry", "rz"]:
                cprint(
                    f"Cannot read camera map {filename} as headings don't match",
                    format=Col.FAIL,
                )
                return False

            for i in range(1, len(lines)):

                line = lines[i].strip()

                values = parse(
                    "{camera_id:^d},{x:^f},{y:^f},{z:^f},{rw:^f},{rx:^f},{ry:^f},{rz:^f}",
                    line,
                )
                if values is not None:
                    pos = [values.named["x"], values.named["y"], values.named["z"]]
                    rot = [values.named["rw"], values.named["rx"], values.named["ry"], values.named["rz"]]
                    self.cameras[values.named["camera_id"]] = {"position": pos, "rotation": rot}

                else:
                    cprint(
                        f"Failed to read line {i} of {filename}: {line}",
                        format=Col.WARNING,
                    )
                    continue

        cprint(f"Read {len(self.cameras)} lines from camera map {filename}...")
        return True

    def write_to_file(self, filename):
        cprint(
            f"Writing camera map with {len(self.cameras)} leds to {filename}...",
            format=Col.BLUE,
        )

        lines = ["camera_id,x,y,z,rw,rx,ry,rz"]

        for camera_id in sorted(self.cameras.keys()):
            lines.append(
                f"{camera_id},"
                f"{self.cameras[camera_id]['position'][0]:f},"
                f"{self.cameras[camera_id]['position'][1]:f},"
                f"{self.cameras[camera_id]['position'][2]:f},"
                f"{self.cameras[camera_id]['rotation'][0]:f},"
                f"{self.cameras[camera_id]['rotation'][1]:f},"
                f"{self.cameras[camera_id]['rotation'][2]:f},"
                f"{self.cameras[camera_id]['rotation'][3]:f}"
            )

        with open(filename, "w") as f:
            f.write("\n".join(lines))

    def add_cam(self, cam_id, position, rotation):
        self.cameras[cam_id] = {"position" : position, "rotation" : rotation}

    def get_cam(self, cam_id):
        return self.cameras[cam_id]