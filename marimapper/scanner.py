# DO NOT MOVE THIS
# FATAL WEIRD CRASH IF THIS ISN'T IMPORTED FIRST DON'T ASK
from marimapper.sfm_process import SFM

from tqdm import tqdm
from pathlib import Path
from marimapper.detector_process import DetectorProcess
from marimapper.queues import Queue2D, DetectionControlEnum
from multiprocessing import get_logger
from marimapper.file_tools import get_all_2d_led_maps
from marimapper.utils import get_user_confirmation
from marimapper.visualize_process import VisualiseProcess
from marimapper.led import last_view
from marimapper.file_writer_process import FileWriterProcess

logger = get_logger()


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
        backend: str,
        server: str,
        led_start: int,
        led_end: int,
        max_fill: int,
        check_movement: bool,
        fast: bool,
    ):
        logger.debug("initialising scanner")
        self.output_dir = output_dir

        self.detector = DetectorProcess(
            device, exposure, threshold, backend, server, check_movement, fast
        )

        self.file_writer = FileWriterProcess(self.output_dir)

        existing_leds = get_all_2d_led_maps(self.output_dir)

        self.sfm = SFM(max_fill, existing_leds)

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

    def wait_for_scan(self):

        with tqdm(
            total=self.led_id_range.stop - self.led_id_range.start,
            unit="LEDs",
            desc="Capturing sequence",
            smoothing=0,
        ) as progress_bar:

            while True:

                control, data = self.detector_update_queue.get()

                if control == DetectionControlEnum.FAIL:
                    logger.error("Scan failed")
                    return False

                if control in [DetectionControlEnum.DETECT, DetectionControlEnum.SKIP]:
                    progress_bar.update(1)
                    progress_bar.refresh()

                if control == DetectionControlEnum.DONE:
                    done_view = data
                    logger.info(f"Scan complete {done_view}")
                    return True

                if control == DetectionControlEnum.DELETE:
                    view_id = data
                    logger.info(f"Deleting scan {view_id}")
                    return False

    def mainloop(self):

        while True:

            start_scan = get_user_confirmation("Start scan? [y/n]: ")

            if not start_scan:
                print("Exiting Marimapper, please wait")
                return

            self.check_for_crash()

            if len(self.led_id_range) == 0:
                print(
                    "LED range is zero, have you chosen a backend with 'marimapper --backend'?"
                )
                continue

            self.detector.detect(
                self.led_id_range.start, self.led_id_range.stop, self.current_view
            )

            success = self.wait_for_scan()

            if success:
                self.current_view += 1
