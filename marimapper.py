import argparse
import os
import time
from tqdm import tqdm
from pathlib import Path
import logging

from lib.reconstructor import Reconstructor
from lib import utils
from lib.utils import cprint, Col, get_user_confirmation
from lib.led_map_2d import LEDMap2D
from lib.sfm.sfm import SFM
from lib.visualize_model import Renderer3D


# PYCHARM DEVELOPER WARNING!
# You MUST enabled "Emulate terminal in output console" in the run configuration or
# really weird  stuff happens with multiprocessing!


class MariMapper:

    def __init__(self, args):
        self.led_backend = utils.get_backend(args.backend, args.server)
        os.makedirs(args.output_dir, exist_ok=True)

        self.reconstructor = Reconstructor(
            args.device,
            args.exposure,
            args.threshold,
            self.led_backend,
            width=args.width,
            height=args.height,
        )

        self.renderer3d = Renderer3D(Path(args.output_dir) / "led_map_3d.csv")
        self.sfm = SFM(
            Path(args.output_dir),
            rescale=True,
            interpolate=True,
            event_on_update=self.renderer3d.reload_event,
        )

        self.sfm.start()
        self.renderer3d.start()

    def __del__(self):

        self.sfm.shutdown()
        self.renderer3d.shutdown()
        self.sfm.join()
        self.renderer3d.join()

    def mainloop(self):

        while True:

            self.reconstructor.light()
            self.reconstructor.open_live_feed()
            cprint("Start scan? [y/n]", Col.PURPLE)

            start_scan = get_user_confirmation()

            self.reconstructor.close_live_feed()

            if not start_scan:
                break

            self.reconstructor.dark()

            # The filename is made out of the date, then the resolution of the camera
            string_time = time.strftime("%Y%m%d-%H%M%S")

            filepath = os.path.join(args.output_dir, f"led_map_2d_{string_time}.csv")

            led_map_2d = LEDMap2D()

            total_leds_found = 0

            visible_leds = []

            led_count = self.led_backend.get_led_count()

            last_camera_motion_check_time = time.time()
            camera_motion_interval_sec = 5

            capture_success = True

            for led_id in tqdm(
                range(led_count),
                unit="LEDs",
                desc=f"Capturing sequence to {filepath}",
                total=led_count,
                smoothing=0,
            ):

                result = self.reconstructor.enable_and_find_led(led_id, debug=True)

                if result:
                    visible_leds.append(led_id)
                    led_map_2d.add_detection(led_id, result)
                    total_leds_found += 1

                is_last = led_id == led_count - 1
                camera_motion_check_overdue = (
                    time.time() - last_camera_motion_check_time
                ) > camera_motion_interval_sec

                if camera_motion_check_overdue or is_last:
                    camera_motion = self.reconstructor.get_camera_motion(
                        visible_leds, led_map_2d
                    )
                    last_camera_motion_check_time = time.time()

                    if camera_motion > 1.0:
                        cprint(
                            f"\nFailed to capture sequence as camera moved by {int(camera_motion)}%",
                            format=Col.FAIL,
                        )
                        capture_success = False
                        break

            if capture_success:
                led_map_2d.write_to_file(filepath)
                cprint(f"{total_leds_found}/{led_count} leds found", Col.BLUE)

                self.sfm.reload()


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    logging.info("Starting MariMapper")

    parser = argparse.ArgumentParser(description="Captures LED flashes to file")

    utils.add_camera_args(parser)
    utils.add_backend_args(parser)

    parser.add_argument(
        "output_dir",
        type=str,
        help="The output folder for your capture",
    )

    args = parser.parse_args()

    marimapper = MariMapper(args=args)

    marimapper.mainloop()
