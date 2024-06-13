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
            self._vis.add_geometry(self.point_cloud, reset_bounding_box=True)

        self._vis.update_geometry(self.point_cloud)

        self.reload_event.clear()
        logging.debug("Renderer3D process reloaded geometry")


def draw_camera(K, R, t, w, h):
    """Create axis, plane and pyramed geometries in Open3D format.
    :param K: calibration matrix (camera intrinsics)
    :param R: rotation matrix
    :param t: translation
    :param w: image width
    :param h: image height
    :return: camera model geometries (axis, plane and pyramid)
    """

    # scale = 1
    color = [0.8, 0.8, 0.8]

    # intrinsics
    K = K.copy()
    Kinv = np.linalg.inv(K)

    # 4x4 transformation
    T = np.column_stack((R, t))
    T = np.vstack((T, (0, 0, 0, 1)))

    # axis
    # axis = open3d.geometry.TriangleMesh.create_coordinate_frame(size=0.5 * scale)
    # axis.transform(T)

    # points in pixel
    points_pixel = [
        [0, 0, 0],
        [0, 0, 1],
        [w, 0, 1],
        [0, h, 1],
        [w, h, 1],
    ]

    # pixel to camera coordinate system
    points = [Kinv @ p for p in points_pixel]

    # pyramid
    points_in_world = [(R @ p + t) for p in points]
    lines = [
        [0, 1],
        [0, 2],
        [0, 3],
        [0, 4],
    ]
    colors = [color for _ in range(len(lines))]
    line_set = open3d.geometry.LineSet(
        points=open3d.utility.Vector3dVector(points_in_world),
        lines=open3d.utility.Vector2iVector(lines),
    )
    line_set.colors = open3d.utility.Vector3dVector(colors)

    # return as list in Open3D format
    return [line_set]
