import argparse
import os
import time
import signal
from tqdm import tqdm
from pathlib import Path

from lib.reconstructor import Reconstructor
from lib import utils
from lib import logging
from lib.utils import get_user_confirmation
from lib.led_map_2d import LEDMap2D
from lib.sfm.sfm import SFM
from lib.visualize_model import Renderer3D
from multiprocessing import Queue
from lib.led_map_2d import get_all_2d_led_maps


# PYCHARM DEVELOPER WARNING!
# You MUST enable "Emulate terminal in output console" in the run configuration or
# really weird  stuff happens with multiprocessing!


class MariMapper:

    def __init__(self, cli_args):
        self.led_backend = utils.get_backend(cli_args.backend, cli_args.server)
        os.makedirs(args.output_dir, exist_ok=True)

        self.led_map_2d_queue = Queue()
        self.led_map_3d_queue = Queue()

        self.reconstructor = Reconstructor(
            cli_args.device,
            cli_args.exposure,
            cli_args.threshold,
            self.led_backend,
            width=cli_args.width,
            height=cli_args.height,
        )

        self.renderer3d = Renderer3D(led_map_3d_queue=self.led_map_3d_queue)
        self.sfm = SFM(
            Path(cli_args.output_dir),
            rescale=True,
            interpolate=True,
            event_on_update=self.renderer3d.reload_event,
            led_map_2d_queue=self.led_map_2d_queue,
            led_map_3d_queue=self.led_map_3d_queue,
        )

        self.led_maps_2d = get_all_2d_led_maps(Path(cli_args.output_dir))

        self.sfm.add_led_maps_2d(self.led_maps_2d)

        self.sfm.start()
        self.renderer3d.start()

    def close(self):
        logging.debug("marimapper closing")
        self.sfm.shutdown()
        self.renderer3d.shutdown()
        self.sfm.join()
        self.renderer3d.join()
        self.sfm.terminate()
        self.renderer3d.terminate()
        self.reconstructor.close()
        logging.debug("marimapper closed")

    def mainloop(self):

        while True:

            self.reconstructor.light()
            self.reconstructor.open_live_feed()

            start_scan = get_user_confirmation("Start scan? [y/n]: ")

            self.reconstructor.close_live_feed()

            if not start_scan:
                return

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
                        logging.error(
                            f"\nFailed to capture sequence as camera moved by {int(camera_motion)}%"
                        )
                        capture_success = False
                        break

            if capture_success:
                led_map_2d.write_to_file(filepath)
                logging.info(f"{total_leds_found}/{led_count} leds found")

                self.led_maps_2d.append(led_map_2d)
                self.sfm.add_led_maps_2d(self.led_maps_2d)
                self.sfm.reload()


if __name__ == "__main__":

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

    marimapper = MariMapper(cli_args=args)

    marimapper.mainloop()
    marimapper.close()

    # For some reason python refuses to actually exit here, so I'm brute forcing it
    os.kill(os.getpid(), signal.SIGINT)
    os.kill(os.getpid(), signal.CTRL_C_EVENT)
