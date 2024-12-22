# DO NOT MOVE THIS
# FATAL WEIRD CRASH IF THIS ISN'T IMPORTED FIRST DON'T ASK
from marimapper.sfm_process import SFM

from tqdm import tqdm
from pathlib import Path
from marimapper.detector_process import DetectorProcess, DetectionControlEnum
from multiprocessing import get_logger, Queue
from marimapper.file_tools import get_all_2d_led_maps
from marimapper.utils import get_user_confirmation
from marimapper.visualize_process import VisualiseProcess
from marimapper.led import last_view
from marimapper.file_writer_process import FileWriterProcess

logger = get_logger()


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
    ):
        logger.debug("initialising scanner")
        self.output_dir = output_dir

        self.detector = DetectorProcess(
            device,
            exposure,
            threshold,
            backend,
            server,
        )

        self.file_writer = FileWriterProcess(self.output_dir)

        existing_leds = get_all_2d_led_maps(self.output_dir)

        self.sfm = SFM(max_fill, existing_leds)

        self.current_view = last_view(existing_leds) + 1

        self.renderer3d = VisualiseProcess()

        self.detector_update_queue = Queue()

        self.detector.add_output_queue(self.sfm.get_input_queue())
        self.detector.add_output_queue(self.detector_update_queue)
        self.detector.add_output_queue(self.file_writer.get_2d_input_queue())

        self.sfm.add_output_queue(self.renderer3d.get_input_queue())
        self.sfm.add_output_queue(self.file_writer.get_3d_input_queue())
        self.sfm.start()
        self.renderer3d.start()
        self.detector.start()
        self.file_writer.start()

        self.led_id_range = range(
            led_start, min(led_end, self.detector.get_led_count())
        )

        logger.debug("scanner initialised")

    def close(self):
        logger.debug("scanner closing")

        self.detector.stop()
        self.sfm.stop()
        self.renderer3d.stop()
        self.file_writer.stop()

        self.sfm.join()
        self.renderer3d.join()
        self.detector.join()
        self.file_writer.join()
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

                if control == DetectionControlEnum.DETECT:
                    led = data
                    progress = led.led_id - self.led_id_range.start

                    progress_bar.update(progress)
                    progress_bar.refresh()

                if control == DetectionControlEnum.DONE:
                    done_view = data
                    assert done_view == self.current_view
                    return True

                if control == DetectionControlEnum.DELETE:
                    return False

    def mainloop(self):

        while True:

            start_scan = get_user_confirmation("Start scan? [y/n]: ")

            if not start_scan:
                print("Exiting Marimapper")
                return

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
