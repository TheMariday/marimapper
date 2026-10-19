# DO NOT MOVE THIS
# FATAL WEIRD CRASH IF THIS ISN'T IMPORTED FIRST DON'T ASK
from marimapper.sfm_process import SFM

from pathlib import Path
from marimapper.detector_process import DetectorProcess
from marimapper.queues import Queue2D, DetectionControlEnum
from marimapper.scan_progress import RED, CameraStats, ScanDisplay, colour
from multiprocessing import get_logger, set_start_method
from marimapper.file_tools import get_all_2d_led_maps
from marimapper.utils import get_user_confirmation
from marimapper.visualize_process import VisualiseProcess
from marimapper.led import last_view
from marimapper.file_writer_process import FileWriterProcess
from functools import partial

# This is to do with an issue with open3d bug in estimate normals
# https://github.com/isl-org/Open3D/issues/1428
# if left to its default fork start method, add_normals in sfm_process will fail
# add_normals is also in the wrong file, it should be in sfm.py, but this causes a dependancy crash
# I think there is something very wrong with open3d.geometry.PointCloud.estimate_normals()
# See https://github.com/TheMariday/marimapper/issues/46
# I would prefer not to call this here as it means that any process being called after this will have a different
# spawn method, however it makes tests more robust in isolation
# This is only an issue on Linux, as on Windows and Mac, the default start method is spawn

logger = get_logger()

# after this many leds, a camera that hasn't seen a single one gets a hint about what to check
NO_DETECTION_WARNING_AFTER = 20


def join_with_warning(process_to_join, process_name, timeout=10):
    logger.debug(f"{process_name} stopping...")
    process_to_join.join(
        timeout=timeout
    )  # Strangely the return code for join does not match the exitcode attribute

    if process_to_join.exitcode is None:
        logger.warning(f"{process_name} failed to stop, some data might be lost")
        return
    if process_to_join.exitcode != 0:
        logger.warning(
            f"{process_name} failed to stop with exit code {process_to_join.exitcode}, some data might be lost"
        )
        return

    logger.debug(f"{process_name} stopped")


class Scanner:

    def __init__(
        self,
        output_dir: Path,
        device: str,
        exposure: int,
        threshold: int,
        backend_factory: partial,
        led_start: int,
        led_end: int,
        interpolation_max_fill: int,
        interpolation_max_error: float,
        check_movement: bool,
        camera_model_name: str,
    ):
        logger.debug("initialising scanner")
        set_start_method("spawn")  # VERY important, see top of file
        self.output_dir = output_dir

        # how many cameras capture each scan, and how far leds may be apart to be filled in
        self.view_count = 1
        self.interpolation_max_fill = interpolation_max_fill

        self.detector = DetectorProcess(
            device=device,
            dark_exposure=exposure,
            threshold=threshold,
            backend_factory=backend_factory,
            display=True,
            check_movement=check_movement,
        )

        self.file_writer = FileWriterProcess(self.output_dir)

        existing_leds = get_all_2d_led_maps(self.output_dir)

        led_count = led_end - led_start

        self.sfm = SFM(
            interpolation_max_fill,
            interpolation_max_error,
            existing_leds,
            led_count,
            camera_model_name=camera_model_name,
            camera_fov=60,
        )

        self.current_view = last_view(existing_leds) + 1

        self.renderer3d = VisualiseProcess()

        self.detector_update_queue = Queue2D()

        self.detector.add_output_queue(self.sfm.get_input_queue())
        self.detector.add_output_queue(self.detector_update_queue)
        self.detector.add_output_queue(self.file_writer.get_2d_input_queue())

        self.sfm.add_output_queue(self.renderer3d.get_input_queue())
        self.sfm.add_output_queue(self.file_writer.get_3d_input_queue())
        self.sfm.add_output_info_queue(self.detector.get_input_3d_info_queue())
        self.sfm.start()
        self.renderer3d.start()
        self.detector.start()
        self.file_writer.start()

        # we add plus one here as I assume people want to include the last led they define
        self.led_id_range = range(
            led_start, min(led_end + 1, self.detector.get_led_count())
        )

        logger.debug("scanner initialised")

    def check_for_crash(self):
        if not self.detector.is_alive():
            raise Exception("LED Detector has stopped unexpectedly")

        if not self.sfm.is_alive():
            raise Exception("SFM has stopped unexpectedly")

        if not self.renderer3d.is_alive():
            raise Exception("Visualiser has stopped unexpectedly")

        if not self.file_writer.is_alive():
            raise Exception("File writer has stopped unexpectedly")

    def close(self):
        logger.debug("scanner closing")

        self.detector.stop()
        self.sfm.stop()
        self.renderer3d.stop()
        self.file_writer.stop()

        join_with_warning(self.detector, "detector")
        join_with_warning(self.sfm, "SFM")
        join_with_warning(self.file_writer, "File Writer")
        join_with_warning(self.renderer3d, "Visualiser")

        logger.debug("scanner closed")

    def camera_label(self, camera: int) -> str:
        return "The camera" if self.view_count == 1 else f"Camera {camera + 1}"

    def wait_for_scan(self):

        # each camera finishes its own view, so there is one DONE or DELETE for every camera
        views_unfinished = self.view_count
        any_view_complete = False

        led_count = self.led_id_range.stop - self.led_id_range.start
        stats = [CameraStats() for _ in range(self.view_count)]
        events = 0
        warned = set()

        # a line for the whole scan, then one for every camera showing how many leds that camera has
        # detected so far and where it has gaps
        display = ScanDisplay(led_count, self.view_count)
        display.draw(0, stats, self.interpolation_max_fill)

        while True:

            control, data = self.detector_update_queue.get()

            if control == DetectionControlEnum.FAIL:
                logger.error("Scan failed")
                return False

            if control in [DetectionControlEnum.DETECT, DetectionControlEnum.SKIP]:
                # for every led the detector reports one result per camera, in camera order
                camera = events % self.view_count
                events += 1

                found = control == DetectionControlEnum.DETECT
                stats[camera].add(data.led_id if found else data, found)

                leds_tried = events // self.view_count  # leds every camera has reported
                display.draw(leds_tried, stats, self.interpolation_max_fill)

                for camera, camera_stats in enumerate(stats):
                    if (
                        camera_stats.detected == 0
                        and leds_tried >= NO_DETECTION_WARNING_AFTER
                        and camera not in warned
                    ):
                        warned.add(camera)
                        display.write(
                            f"{self.camera_label(camera)} hasn't detected any of the first "
                            f"{NO_DETECTION_WARNING_AFTER} LEDs yet. If it should see them, check that it "
                            f"can and that the room is dark (marimapper_check_camera shows what it sees), "
                            f"then try a higher --exposure (e.g. -8) or a lower --threshold"
                        )

            if control == DetectionControlEnum.DONE:
                done_view = data
                logger.info(f"Scan complete {done_view}")
                any_view_complete = True
                views_unfinished -= 1

            if control == DetectionControlEnum.DELETE:
                view_id = data
                logger.info(f"Deleting scan {view_id}")
                views_unfinished -= 1

            if views_unfinished == 0:
                display.finish(
                    events // self.view_count, stats, self.interpolation_max_fill
                )

                # point out the gaps the reconstruction won't be able to fill in by itself
                for camera, camera_stats in enumerate(stats):
                    for line in camera_stats.report(self.interpolation_max_fill):
                        print(
                            colour(
                                f"{self.camera_label(camera)}: {line}",
                                RED,
                                display.interactive,
                            )
                        )

                return any_view_complete

    def mainloop(self):

        while True:

            start_scan = get_user_confirmation("Start scan? [y/n]: ")

            if not start_scan:
                print("Exiting Marimapper, please wait")
                return

            self.check_for_crash()

            if len(self.led_id_range) == 0:
                print("LED range is zero, are you using a dummy backend?")
                continue

            self.detector.detect(
                self.led_id_range.start, self.led_id_range.stop, self.current_view
            )

            success = self.wait_for_scan()

            if success:
                self.current_view += 1
