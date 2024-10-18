# DO NOT MOVE THIS
# FATAL WEIRD CRASH IF THIS ISN'T IMPORTED FIRST DON'T ASK
from marimapper.sfm_process import SFM

import os
import time
from tqdm import tqdm
from pathlib import Path
from marimapper.detector_process import DetectorProcess
from marimapper import multiprocessing_logging
from marimapper.file_tools import get_all_2d_led_maps, write_2d_leds_to_file
from marimapper.utils import get_user_confirmation
from marimapper.visualize_model import Renderer3D
from multiprocessing import Queue

class Scanner:

    def __init__(self, cli_args):
        self.output_dir = cli_args.dir
        os.makedirs(self.output_dir, exist_ok=True)

        self.led_id_range = range(cli_args.start, cli_args.end)

        self.led_map_2d_queue = Queue()
        self.led_map_3d_queue = Queue()

        self.detector = DetectorProcess(
            cli_args.device,
            cli_args.exposure,
            cli_args.threshold,
            cli_args.backend,
            cli_args.server,
        )

        self.renderer3d = Renderer3D(led_map_3d_queue=self.led_map_3d_queue)
        self.sfm = SFM(self.led_map_2d_queue,self.led_map_3d_queue)

        self.leds_2d = get_all_2d_led_maps(Path(self.output_dir))

        for led in self.leds_2d:
            self.led_map_2d_queue.put(led)

        self.sfm.start()
        self.renderer3d.start()
        self.detector.start()

    def close(self):
        multiprocessing_logging.debug("marimapper closing")
        self.sfm.shutdown()
        self.renderer3d.shutdown()
        self.detector.shutdown()

        self.sfm.join()
        self.renderer3d.join()
        self.detector.join()

        self.sfm.terminate()
        self.renderer3d.terminate()
        self.detector.terminate()
        multiprocessing_logging.debug("marimapper closed")

    def mainloop(self):

        while True:

            start_scan = get_user_confirmation("Start scan? [y/n]: ")

            if not start_scan:
                return

            self.detector.detection_request.put(-1)
            result = self.detector.detection_result.get()
            if result.valid():
                multiprocessing_logging.error(
                    f"All LEDs should be off, but the detector found one at {result.pos()}"
                )
                continue

            # The filename is made out of the date, then the resolution of the camera
            string_time = time.strftime("%Y%m%d-%H%M%S")

            filepath = os.path.join(self.output_dir, f"led_map_2d_{string_time}.csv")

            leds = []

            view_id = 0  # change

            for led_id in self.led_id_range:
                self.detector.detection_request.put((view_id, led_id))

            for _ in tqdm(
                self.led_id_range,
                unit="LEDs",
                desc=f"Capturing sequence to {filepath}",
                total=self.led_id_range.stop,
                smoothing=0,
            ):
                led = self.detector.detection_result.get(timeout=10)
                print(f"found {led}")

                leds.append(led)

                self.led_map_2d_queue.put(led)

            write_2d_leds_to_file(leds, filepath)
