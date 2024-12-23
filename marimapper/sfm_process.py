from multiprocessing import Process, Event, get_logger
from marimapper.led import (
    rescale,
    recenter,
    LED3D,
    fill_gaps,
    get_leds_with_view,
    LED2D,
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


def sanity_check(leds_2d, leds_3d, view) -> None:

    if len(leds_2d) == 0 or len(leds_3d) == 0:
        return

    leds_3d_ids = set([led.led_id for led in leds_3d])
    view_ids = [led.led_id for led in get_leds_with_view(leds_2d, view)]
    overlap_len = len(leds_3d_ids.intersection(view_ids))
    overlap_percentage = int((overlap_len / len(view_ids)) * 100)

    logger.debug(f"scan {view} has overlap of {overlap_len} or {overlap_percentage}%")

    if overlap_len < 10:
        logger.error(
            f"Scan {view} has a very low overlap with the reconstructed model "
            f"(only {overlap_len} points) and therefore may have been disregarded"
        )
    if overlap_percentage < 0.5:
        logger.warning(
            f"Scan {view} has a low overlap with the reconstructed model "
            f"(only {overlap_percentage}%) and therefore may have been disregarded"
        )


class SFM(Process):

    def __init__(
        self, max_fill: int = 5, existing_leds: Union[list[LED2D], None] = None
    ):
        super().__init__()
        self._input_queue: Queue2D = Queue2D()
        self._output_queues: list[Queue3D] = []
        self._exit_event: Event() = Event()
        self.max_fill = max_fill
        self.leds_2d = existing_leds if existing_leds is not None else []

    def get_input_queue(self) -> Queue2D:
        return self._input_queue

    def add_output_queue(self, queue: Queue3D):
        self._output_queues.append(queue)

    def stop(self):
        self._exit_event.set()

    def run(self):

        update_required = len(self.leds_2d) > 0
        check_required = False
        view_id = 0

        while not self._exit_event.is_set():

            while not self._input_queue.empty():
                control, data = self._input_queue.get()
                if control == DetectionControlEnum.DETECT:
                    detection = data
                    if detection.point is not None:  # this is nasty
                        self.leds_2d.append(detection)
                        update_required = True

                if control == DetectionControlEnum.DONE:
                    view_id = data
                    check_required = True

                if control == DetectionControlEnum.DELETE:
                    view_id = data
                    self.leds_2d = [
                        led for led in self.leds_2d if led.view_id != view_id
                    ]

            if update_required:
                update_required = False

                leds_3d = sfm(self.leds_2d)

                if len(leds_3d) == 0:
                    logger.info("Failed to reconstruct any leds")
                    continue

                if check_required:
                    check_required = False
                    sanity_check(self.leds_2d, leds_3d, view_id)

                rescale(leds_3d)

                fill_gaps(leds_3d, max_missing=self.max_fill)

                recenter(leds_3d)

                add_normals(leds_3d)

                for queue in self._output_queues:
                    queue.put(leds_3d)

            else:
                time.sleep(1)
