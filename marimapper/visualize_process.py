import numpy as np
import open3d
from marimapper import logging as logging
from multiprocessing import Process, Event
from marimapper.led import LED3D, View
import time


def get_all_views(leds: list[LED3D]) -> list[View]:
    views = []
    for led in leds:
        for view in led.views:
            if view.view_id not in [v.view_id for v in views]:
                views.append(view)

    return views


class VisualiseProcess(Process):

    def __init__(self, input_queue):
        logging.debug("Renderer3D initialising")
        super().__init__()
        self._vis = None
        self._input_queue = input_queue
        self._exit_event = Event()
        self.point_cloud = None
        self.line_set = None
        self.strip_set = None
        logging.debug("Renderer3D initialised")

    def stop(self):
        self._exit_event.set()

    def run(self):
        logging.debug("Renderer3D process starting")

        # wait for data to arrive sensibly
        while self._input_queue.empty():
            if self._exit_event.is_set():
                return
            time.sleep(0.1)

        self.initialise_visualiser__()
        self.reload_geometry__(True)

        while not self._exit_event.is_set():

            if not self._input_queue.empty():
                self.reload_geometry__()

            self._vis.poll_events()
            self._vis.update_renderer()

    def initialise_visualiser__(self):
        logging.debug("Renderer3D process initialising visualiser")

        self._vis = open3d.visualization.Visualizer()
        self._vis.create_window(
            window_name="MariMapper",
            width=640,
            height=640,
        )

        self.point_cloud = open3d.geometry.PointCloud()
        self.line_set = open3d.geometry.LineSet()
        self.strip_set = open3d.geometry.LineSet()

        view_ctl = self._vis.get_view_control()
        view_ctl.set_up((0, 1, 0))
        view_ctl.set_lookat((0, 0, 0))
        view_ctl.set_zoom(0.3)

        render_options = self._vis.get_render_option()
        render_options.point_show_normal = True
        render_options.point_color_option = (
            open3d.visualization.PointColorOption.YCoordinate
        )
        render_options.background_color = [0.2, 0.2, 0.2]

        logging.debug("Renderer3D process initialised visualiser")

    def reload_geometry__(self, first=False):

        logging.debug("Renderer3D process reloading geometry")

        leds = self._input_queue.get()

        logging.debug(f"Fetched led map with size {len(leds)}")
        all_views = get_all_views(leds)

        p, l, c = view_to_points_lines_colors(all_views)

        self.line_set.points = open3d.utility.Vector3dVector(p)
        self.line_set.lines = open3d.utility.Vector2iVector(l)
        self.line_set.colors = open3d.utility.Vector3dVector(c)

        self.point_cloud.points = open3d.utility.Vector3dVector(
            np.array([led.point.position for led in leds])
        )
        self.point_cloud.normals = open3d.utility.Vector3dVector(
            np.array([led.point.normal for led in leds]) * 0.2
        )

        # self.strip_set.points = self.point_cloud.points
        # self.strip_set.lines = open3d.utility.Vector2iVector(
        #    led_map.get_connected_leds()
        # )
        # self.strip_set.colors = open3d.utility.Vector3dVector(
        #    [[0.8, 0.8, 0.8] for _ in range(len(self.strip_set.lines))]
        # )

        if first:
            self._vis.add_geometry(self.point_cloud)
            self._vis.add_geometry(self.line_set)
            self._vis.add_geometry(self.strip_set)
        else:
            self._vis.update_geometry(self.point_cloud)
            self._vis.update_geometry(self.line_set)
            self._vis.update_geometry(self.strip_set)

        logging.debug("Renderer3D process reloaded geometry")


def view_to_points_lines_colors(views):  # returns points and lines

    all_points = []
    all_lines = []

    camera_scale = 2.0

    camera_cone_points = np.array(
        [[0, 0, 0], [-1, -1, 2], [1, -1, 2], [1, 1, 2], [-1, 1, 2], [0, -1.5, 2]]
    )

    camera_cone_points *= camera_scale

    camera_cone_lines = np.array(
        [[0, 1], [0, 2], [0, 3], [0, 4], [1, 2], [2, 3], [3, 4], [4, 1], [1, 5], [2, 5]]
    )

    for i, view in enumerate(views):

        points_in_world = [
            (view.rotation @ p + view.position) for p in camera_cone_points
        ]

        offset = i * len(camera_cone_points)

        all_points.extend(points_in_world)
        all_lines.extend(camera_cone_lines + offset)

    all_colors = [[0.8, 0.8, 0.8] for _ in range(len(all_lines))]

    return all_points, all_lines, all_colors
