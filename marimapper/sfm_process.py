from multiprocessing import Process, Event
from marimapper.led import LED2D, rescale, recenter, LED3D
from marimapper.sfm import sfm
import open3d
import numpy as np
import math

# this is here for now as there is some weird import dependency going on...
def add_normals(leds: list[LED3D]):

    for led in leds:
        led.point.normal = (1, 1, 1)

    pcd = open3d.geometry.PointCloud()

    xyz = [led.point.position for led in leds]

    pcd.points = open3d.utility.Vector3dVector(xyz)

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

    def __init__(
        self, led_map_2d_queue=None, led_map_3d_queue=None, rescale=True, recenter=True
    ):
        super().__init__()
        self.exit_event = Event()
        self.led_map_3d_queue = led_map_3d_queue
        self.led_map_2d_queue = led_map_2d_queue
        self.rescale = rescale
        self.recenter = recenter
        self.leds: list[LED2D] = []

    def shutdown(self):
        self.exit_event.set()

    def run(self):

        update_required = False

        while not self.exit_event.is_set():
            if self.led_map_2d_queue.empty():

                if not update_required:
                    continue

                leds_3d = sfm(self.leds)

                if len(leds_3d) == 0:
                    continue

                if self.rescale:
                    rescale(leds_3d)

                if self.recenter:
                    recenter(leds_3d)

                add_normals(leds_3d)

                self.led_map_3d_queue.put(leds_3d)
                update_required = False
            else:
                led = self.led_map_2d_queue.get()
                self.leds.append(led)
                update_required = True
