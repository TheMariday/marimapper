import numpy as np
import open3d
from lib import logging
from multiprocessing import Process, Event


class Renderer3D(Process):

    def __init__(self, led_map_3d_queue):
        logging.debug("Renderer3D initialising")
        super().__init__()
        self._vis = None
        self.exit_event = Event()
        self.reload_event = Event()
        self.led_map_3d_queue = led_map_3d_queue
        self.point_cloud = None
        self.line_set = None
        logging.debug("Renderer3D initialised")

    def get_reload_event(self):
        return self.reload_event

    def shutdown(self):
        self.exit_event.set()

    def reload(self):
        logging.debug("Renderer3D reload request sent")
        self.reload_event.set()

    def run(self):
        logging.debug("Renderer3D process starting")

        while not self.reload_event.wait(timeout=1):
            if self.exit_event.is_set():
                return

        self.initialise_visualiser__()
        self.reload_geometry__(True)

        while not self.exit_event.is_set():
            if self.reload_event.is_set():
                self.reload_geometry__()
                logging.debug(
                    "Renderer3D process received reload event, reloading geometry"
                )

            window_closed = not self._vis.poll_events()

            if window_closed:
                logging.debug("Renderer3D process window closed, stopping process")
                self.exit_event.set()

            self._vis.update_renderer()

        self._vis.destroy_window()

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

        led_map = self.led_map_3d_queue.get()

        logging.debug(f"Fetched led map with size {len(led_map.keys())}")

        p, l, c = camera_to_points_lines_colors(led_map.cameras)

        self.line_set.points = open3d.utility.Vector3dVector(p)
        self.line_set.lines = open3d.utility.Vector2iVector(l)
        self.line_set.colors = open3d.utility.Vector3dVector(c)

        xyz = []
        normals = []
        for led_id in led_map.keys():
            xyz.append(led_map[led_id]["pos"])
            normals.append(
                led_map[led_id]["normal"] / np.linalg.norm(led_map[led_id]["normal"])
            )

        self.point_cloud.points = open3d.utility.Vector3dVector(xyz)
        self.point_cloud.normals = open3d.utility.Vector3dVector(normals)

        if first:
            self._vis.add_geometry(self.line_set)
            self._vis.add_geometry(self.point_cloud, reset_bounding_box=True)

        self._vis.update_geometry(self.point_cloud)
        self._vis.update_geometry(self.line_set)

        self.reload_event.clear()
        logging.debug("Renderer3D process reloaded geometry")


def camera_to_points_lines_colors(cameras):  # returns points and lines

    all_points = []
    all_lines = []

    for cam_id, camera in enumerate(cameras):

        R, t = camera

        Kinv = np.array([[0.0005, 0, -0.5], [0, 0.0005, -0.5], [0, 0, 1]])

        # points in pixel
        points_pixel = [
            [0, 0, 0],
            [0, 0, 1],
            [2000, 0, 1],
            [0, 2000, 1],
            [2000, 2000, 1],
        ]

        # pixel to camera coordinate system
        points = [Kinv @ p for p in points_pixel]

        # pyramid
        points_in_world = [(R @ p + t) for p in points]
        offset = cam_id * 5
        lines = [
            [offset, offset + 1],
            [offset, offset + 2],
            [offset, offset + 3],
            [offset, offset + 4],
        ]

        all_points.extend(points_in_world)
        all_lines.extend(lines)

    all_colors = [[0.8, 0.8, 0.8] for _ in range(len(all_lines))]

    return all_points, all_lines, all_colors
