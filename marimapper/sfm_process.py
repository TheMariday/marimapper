from multiprocessing import Process, Event, get_logger
from marimapper.led import (
    rescale,
    recenter,
    LED3D,
    fill_gaps,
    get_overlap_and_percentage,
    LED2D,
    last_view,
)
from marimapper.sfm import sfm
from marimapper.queues import Queue2D, Queue3D, DetectionControlEnum
import open3d
import numpy as np
import math
import time
from typing import Union

logger = get_logger()


# this is here for now as there is some weird import dependency going on...
# See https://github.com/TheMariday/marimapper/issues/46
def add_normals(leds: list[LED3D]):

    pcd = open3d.geometry.PointCloud()

    pcd.points = open3d.utility.Vector3dVector([led.point.position for led in leds])

    pcd.normals = open3d.utility.Vector3dVector(np.zeros((len(leds), 3)))

    pcd.estimate_normals()

    camera_normals = []
    for led in leds:
        views = [view.position for view in led.views]
        camera_normals.append(np.average(views, axis=0) if views else None)

    for led, camera_normal, open3d_normal in zip(leds, camera_normals, pcd.normals):

        led.point.normal = open3d_normal / np.linalg.norm(open3d_normal)

        if camera_normal is not None:

            angle = np.arccos(np.clip(np.dot(camera_normal, open3d_normal), -1.0, 1.0))

            if angle > math.pi / 2.0:
                led.point.normal *= -1


def print_without_hiding_scan_message(message: str):
    print(f"\r{message}\nStart scan? [y/n]: ", end="")


class SFM(Process):

    def __init__(
        self,
        max_fill: int = 5,
        existing_leds: Union[list[LED2D], None] = None,
        led_count: int = 0,
    ):
        super().__init__()
        self._input_queue: Queue2D = Queue2D()
        self._output_queues: list[Queue3D] = []
        self._exit_event = Event()
        self._led_count = led_count
        self.max_fill = max_fill
        self.leds_2d = existing_leds if existing_leds is not None else []
        self.leds_3d: list[LED3D] = []
        self.daemon = True

    def get_input_queue(self) -> Queue2D:
        return self._input_queue

    def add_output_queue(self, queue: Queue3D):
        self._output_queues.append(queue)

    def stop(self):
        self._exit_event.set()

    def run(self):

        needs_initial_reconstruction = len(self.leds_2d) > 0

        while not self._exit_event.is_set():

            update_sfm = False
            print_overlap = False
            print_reconstructed = False

            while not self._input_queue.empty():

                control, data = self._input_queue.get()
                if control == DetectionControlEnum.DETECT:
                    led2d = data
                    self.leds_2d.append(led2d)
                    update_sfm = True
                    print_reconstructed = False

                if control == DetectionControlEnum.DONE:
                    print_overlap = True
                    print_reconstructed = True

                if control == DetectionControlEnum.DELETE:
                    view_id = data
                    self.leds_2d = [
                        led for led in self.leds_2d if led.view_id != view_id
                    ]
                    update_sfm = True

            if (update_sfm or needs_initial_reconstruction) and len(self.leds_2d) > 0:

                self.leds_3d = sfm(self.leds_2d)

                if len(self.leds_3d) > 0:
                    rescale(self.leds_3d)

                    fill_gaps(self.leds_3d, max_missing=self.max_fill)

                    recenter(self.leds_3d)

                    add_normals(self.leds_3d)

                    for queue in self._output_queues:
                        queue.put(self.leds_3d)

            if (print_reconstructed or needs_initial_reconstruction) and len(
                self.leds_3d
            ) > 0:

                print_without_hiding_scan_message(
                    f"Reconstructed {len(self.leds_3d)} / {self._led_count}"
                )

            needs_initial_reconstruction = False

            if print_overlap and len(self.leds_3d) > 0:
                last_view_id = last_view(self.leds_2d)
                overlap, overlap_percentage = get_overlap_and_percentage(
                    self.leds_2d, self.leds_3d, last_view_id
                )

                logger.debug(
                    f"Scan {last_view_id} has overlap of {overlap} or {overlap_percentage}%"
                )

                if overlap < 10:
                    print_without_hiding_scan_message(
                        f"Warning! Scan {last_view_id} has a very low overlap with the reconstructed model "
                        f"(only {overlap} points) and therefore may be disregarded when reconstructing "
                        "unless scans are added between this and the prior scan"
                    )
                if overlap_percentage < 50:
                    print_without_hiding_scan_message(
                        f"Warning! Scan {last_view_id} has a low overlap with the reconstructed model "
                        f"(only {overlap_percentage}%) and therefore may be disregarded when reconstructing "
                        "unless scans are added between this and the prior scan"
                    )

            time.sleep(1)
