from multiprocessing import Process, Event, Queue, get_logger
from marimapper.led import LED2D, rescale, recenter, LED3D
from marimapper.sfm import sfm
import open3d
import numpy as np
import math

logger = get_logger()


# this is here for now as there is some weird import dependency going on...
def add_normals(leds: list[LED3D]):

    pcd = open3d.geometry.PointCloud()

    pcd.points = open3d.utility.Vector3dVector([led.point.position for led in leds])

    pcd.normals = open3d.utility.Vector3dVector(np.zeros((len(leds), 3)))

    pcd.estimate_normals()

    camera_normals = []
    for led in leds:
        views = [view.position for view in led.views]
        camera_normals.append(np.average(views, axis=0))

    for led, camera_normal, open3d_normal in zip(leds, camera_normals, pcd.normals):

        led.point.normal = open3d_normal / np.linalg.norm(open3d_normal)

        angle = np.arccos(np.clip(np.dot(camera_normal, open3d_normal), -1.0, 1.0))

        if angle > math.pi / 2.0:
            led.point.normal *= -1


class SFM(Process):

    def __init__(self):
        super().__init__()
        self._output_queue = Queue()
        self._output_queue.cancel_join_thread()
        self._input_queue = Queue()
        self._input_queue.cancel_join_thread()
        self._exit_event = Event()

    def add_detection(self, led: LED2D):
        self._input_queue.put(led)

    def get_output_queue(self):
        return self._output_queue

    def get_results(self):
        return self._output_queue.get()

    def stop(self):
        self._exit_event.set()

    def run(self):

        update_required = False

        leds_2d = []

        while not self._exit_event.is_set():

            if not self._input_queue.empty():
                led = self._input_queue.get()
                leds_2d.append(led)
                update_required = True

            else:
                if not update_required:
                    continue

                leds_3d = sfm(leds_2d)

                if len(leds_3d) == 0:
                    continue

                add_normals(leds_3d)

                rescale(leds_3d)

                recenter(leds_3d)

                self._output_queue.put(leds_3d)
                update_required = False

        # clear the queues, don't ask why.
        while not self._input_queue.empty():
            self._input_queue.get()
        while not self._output_queue.empty():
            self._output_queue.get()
