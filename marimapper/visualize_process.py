import numpy as np
import viser
from multiprocessing import get_logger, Process, Event
from marimapper.queues import Queue3D
from marimapper.led import LED3D, View, get_next, get_distance
from marimapper.pycolmap_tools.read_write_model import rotmat2qvec
import time

logger = get_logger()


def get_all_views(leds: list[LED3D]) -> list[View]:
    views = []
    for led in leds:
        for view in led.views:
            if view.view_id not in [v.view_id for v in views]:
                views.append(view)

    return views


class VisualiseProcess(Process):

    def __init__(self, camera_fov: int = 60):
        logger.debug("Renderer3D initialising")
        super().__init__()
        self._server = None
        self._camera_fov = camera_fov
        self._view_handles: dict = {}
        self._input_queue = Queue3D()
        self._exit_event = Event()
        self.daemon = True
        logger.debug("Renderer3D initialised")

    def get_input_queue(self) -> Queue3D:
        return self._input_queue

    def stop(self):
        self._exit_event.set()

    def run(self):
        logger.debug("Renderer3D process starting")
        initialised = False

        while not self._exit_event.is_set():

            if not self._input_queue.empty():
                leds = self._input_queue.get()
                if len(leds) < 9:
                    continue

                if not initialised:
                    self.initialise_visualiser__()
                    initialised = True

                self.reload_geometry__(leds)

            if initialised:
                time.sleep(1 / 60)
            else:
                time.sleep(1)

    def initialise_visualiser__(self):
        logger.debug("Renderer3D process initialising visualiser")

        self._server = viser.ViserServer(label="MariMapper")
        self._server.scene.set_up_direction("+y")
        self._server.scene.add_frame(
            "/origin", axes_length=1.0, axes_radius=0.01
        )

        logger.debug("Renderer3D process initialised visualiser")

    def reload_geometry__(self, leds: list[LED3D]):

        logger.debug("Renderer3D process reloading geometry")

        logger.debug(f"Fetched led map with size {len(leds)}")
        all_views = get_all_views(leds)

        # Camera frustums, one scene node per view (built-in viser rendering).
        # The camera model used for reconstruction is square, so aspect == 1.
        current_view_ids = {view.view_id for view in all_views}
        for view_id, handle in list(self._view_handles.items()):
            if view_id not in current_view_ids:
                handle.remove()
                del self._view_handles[view_id]

        for view in all_views:
            self._view_handles[view.view_id] = self._server.scene.add_camera_frustum(
                f"/views/{view.view_id}",
                fov=np.deg2rad(self._camera_fov),
                aspect=1.0,
                scale=0.3,
                color=(204, 204, 204),
                wxyz=rotmat2qvec(view.rotation),
                position=view.position,
            )

        positions = np.array([led.point.position for led in leds])
        colors = np.array([led.get_color() for led in leds])

        self._server.scene.add_point_cloud(
            "/leds",
            points=positions,
            colors=colors,
            point_size=0.05,
        )


        strips = []
        for led_index, led in enumerate(leds):
            next_led = get_next(led, leds)
            if next_led is not None and (next_led.led_id - led.led_id == 1):
                if get_distance(led, next_led) < 1.50:  # + 50%
                    strips.append((led_index, leds.index(next_led)))

        if strips:
            self._server.scene.add_line_segments(
                "/strips",
                points=positions[np.array(strips)],
                colors=(204, 204, 204),
            )

        logger.debug("Renderer3D process reloaded geometry")
