# DO NOT MOVE THIS
# FATAL WEIRD CRASH IF THIS ISN'T IMPORTED FIRST DON'T ASK
from marimapper.sfm_process import SFM

import os
import time
from tqdm import tqdm
from pathlib import Path
from marimapper.detector_process import DetectorProcess
from marimapper import logging
from marimapper.file_tools import get_all_2d_led_maps, write_2d_leds_to_file
from marimapper.utils import get_user_confirmation
from marimapper.visualize_process import VisualiseProcess
from multiprocessing import Queue
from marimapper.led import last_view


class Scanner:

    def __init__(self, cli_args):
        self.output_dir = cli_args.dir
        os.makedirs(self.output_dir, exist_ok=True)

        self.led_id_range = range(cli_args.start, cli_args.end)

        self.led_map_3d_queue = Queue()

        self.detector = DetectorProcess(
            cli_args.device,
            cli_args.exposure,
            cli_args.threshold,
            cli_args.backend,
            cli_args.server,
        )

        self.sfm = SFM()

        self.leds = get_all_2d_led_maps(Path(self.output_dir))
        for led in self.leds:
            self.sfm.add_detection(led)

        self.current_view = last_view(self.leds) + 1

        self.renderer3d = VisualiseProcess(input_queue=self.sfm.get_output_queue())

        self.sfm.start()
        self.renderer3d.start()
        self.detector.start()

    def close(self):
        logging.debug("marimapper closing")

        self.detector.stop()
        self.sfm.stop()
        self.renderer3d.stop()

        self.sfm.join()
        self.renderer3d.join()
        self.detector.join()

        logging.debug("marimapper closed")

    def mainloop(self):

        while True:

            start_scan = get_user_confirmation("Start scan? [y/n]: ")

            if not start_scan:
                return

            leds = []

            for led_id in self.led_id_range:
                self.detector.detect(led_id, self.current_view)

            for _ in tqdm(
                self.led_id_range,
                unit="LEDs",
                desc="Capturing sequence",
                total=self.led_id_range.stop,
                smoothing=0,
            ):
                led = self.detector.get_results()

                if led.point is None:
                    continue

                print(f"found {led}")

                leds.append(led)

                self.sfm.add_detection(led)

            self.current_view += 1

            # The filename is made out of the date, then the resolution of the camera
            string_time = time.strftime("%Y%m%d-%H%M%S")
            filepath = os.path.join(self.output_dir, f"led_map_2d_{string_time}.csv")
            write_2d_leds_to_file(leds, filepath)
