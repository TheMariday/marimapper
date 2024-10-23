# DO NOT MOVE THIS
# FATAL WEIRD CRASH IF THIS ISN'T IMPORTED FIRST DON'T ASK
from marimapper.sfm_process import SFM

import os
from tqdm import tqdm
from pathlib import Path
from marimapper.detector_process import DetectorProcess
from multiprocessing import get_logger, Queue
from marimapper.file_tools import get_all_2d_led_maps
from marimapper.utils import get_user_confirmation
from marimapper.visualize_process import VisualiseProcess
from marimapper.led import last_view
from marimapper.file_writer_process import FileWriterProcess

logger = get_logger()


class Scanner:

    def __init__(self, cli_args):
        logger.debug("initialising scanner")
        self.output_dir = Path(cli_args.dir)
        os.makedirs(self.output_dir, exist_ok=True)

        self.detector = DetectorProcess(
            cli_args.device,
            cli_args.exposure,
            cli_args.threshold,
            cli_args.backend,
            cli_args.server,
        )

        self.sfm = SFM()

        self.file_writer = FileWriterProcess(self.output_dir)

        leds = get_all_2d_led_maps(self.output_dir)

        for led in leds:
            self.sfm.add_detection(led)

        self.current_view = last_view(leds) + 1

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
            cli_args.start, min(cli_args.end, self.detector.get_led_count())
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

    def mainloop(self):

        while True:

            start_scan = get_user_confirmation("Start scan? [y/n]: ")

            if not start_scan:
                print("exiting")
                return

            for led_id in self.led_id_range:
                self.detector.detect(led_id, self.current_view)

            for _ in tqdm(
                self.led_id_range,
                unit="LEDs",
                desc="Capturing sequence",
                total=self.led_id_range.stop,
                smoothing=0,
            ):
                self.detector_update_queue.get()

            self.current_view += 1
