from multiprocessing import Process, Event, Queue, get_logger
from marimapper.led import LED2D, rescale, recenter, LED3D, fill_gaps
from marimapper.sfm import sfm
import open3d
import numpy as np
import math
import time

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


class SFM(Process):

    def __init__(self, max_fill=5):
        super().__init__()
        self._input_queue = Queue()
        self._input_queue.cancel_join_thread()
        self._output_queues: list[Queue] = []
        self._exit_event = Event()
        self.max_fill = max_fill

    def get_input_queue(self) -> Queue:
        return self._input_queue

    def add_detection(self, led: LED2D):
        self._input_queue.put(led)

    def add_output_queue(self, queue: Queue):
        self._output_queues.append(queue)

    def stop(self):
        self._exit_event.set()

    def run(self):

        update_required = False

        leds_2d = []

        while not self._exit_event.is_set():

            while not self._input_queue.empty():
                led: LED2D = self._input_queue.get()
                if led.point is not None:
                    leds_2d.append(led)
                    update_required = True

            if update_required:
                update_required = False

                leds_3d = sfm(leds_2d)

                if len(leds_3d) == 0:
                    logger.info("Failed to reconstruct any leds")
                    continue

                rescale(leds_3d)

                fill_gaps(leds_3d, max_missing=self.max_fill)

                recenter(leds_3d)

                add_normals(leds_3d)

                for queue in self._output_queues:
                    queue.put(leds_3d)

            else:
                time.sleep(1)

        # clear the queues, don't ask why.
        while not self._input_queue.empty():
            self._input_queue.get()
        for queue in self._output_queues:
            while not queue.empty():
                queue.get()
