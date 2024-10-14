import os
import time
from tqdm import tqdm
from pathlib import Path

from marimapper.detector import Detector
from marimapper import utils
from marimapper import logging
from marimapper.utils import get_user_confirmation
from marimapper.led_map_2d import LEDMap2D
from marimapper.sfm import SFM
from marimapper.visualize_model import Renderer3D
from multiprocessing import Queue
from marimapper.led_map_2d import get_all_2d_led_maps


class Scanner:

    def __init__(self, cli_args):
        self.output_dir = cli_args.dir
        self.led_backend = utils.get_backend(cli_args.backend, cli_args.server)
        if self.led_backend is not None:
            self.led_id_range = range(
                cli_args.start, min(cli_args.end, self.led_backend.get_led_count())
            )
        os.makedirs(self.output_dir, exist_ok=True)
        self.led_map_2d_queue = Queue()
        self.led_map_3d_queue = Queue()

        self.detector = Detector(
            cli_args.device, cli_args.exposure, cli_args.threshold, self.led_backend
        )

        self.renderer3d = Renderer3D(led_map_3d_queue=self.led_map_3d_queue)
        self.sfm = SFM(
            Path(self.output_dir),
            rescale=True,
            interpolate=True,
            event_on_update=self.renderer3d.reload_event,
            led_map_2d_queue=self.led_map_2d_queue,
            led_map_3d_queue=self.led_map_3d_queue,
        )

        self.led_maps_2d = get_all_2d_led_maps(Path(self.output_dir))

        self.sfm.add_led_maps_2d(self.led_maps_2d)

        self.sfm.start()
        self.renderer3d.start()
        self.detector.start()

    def close(self):
        logging.debug("marimapper closing")
        self.sfm.shutdown()
        self.renderer3d.shutdown()
        self.detector.shutdown()

        self.sfm.join()
        self.renderer3d.join()
        self.detector.join()

        self.sfm.terminate()
        self.renderer3d.terminate()
        self.detector.terminate()
        logging.debug("marimapper closed")

    def mainloop(self):

        while True:

            start_scan = get_user_confirmation("Start scan? [y/n]: ")

            if not start_scan:
                return

            if self.led_backend is None:
                logging.warn(
                    "Cannot start backend as no backend has been defined. Re-run marimapper with --backend <backend name>"
                )
                return

            self.detector.detection_request.put(-1)
            result = self.detector.detection_result.get()
            if result.valid():
                logging.error(
                    f"All LEDs should be off, but the detector found one at {result.pos()}"
                )
                continue

            # The filename is made out of the date, then the resolution of the camera
            string_time = time.strftime("%Y%m%d-%H%M%S")

            filepath = os.path.join(self.output_dir, f"led_map_2d_{string_time}.csv")

            led_map_2d = LEDMap2D()

            for led_id in self.led_id_range:
                self.detector.detection_request.put(led_id)

            for _ in tqdm(
                self.led_id_range,
                unit="LEDs",
                desc=f"Capturing sequence to {filepath}",
                total=self.led_id_range.stop,
                smoothing=0,
            ):
                result = self.detector.detection_result.get(timeout=10)
                print(f"found {result}")

                led_map_2d.add_detection(result)

            led_map_2d.write_to_file(filepath)

            self.led_maps_2d.append(led_map_2d)
            self.sfm.add_led_maps_2d(self.led_maps_2d)
            self.sfm.reload()
