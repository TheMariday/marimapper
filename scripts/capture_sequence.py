import argparse
import os
import sys
import time

from tqdm import tqdm

sys.path.append("./")

from lib.reconstructor import Reconstructor
from lib import utils
from lib.map_read_write import write_2d_map
from lib.utils import cprint, Col, get_user_confirmation


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Captures LED flashes to file")

    utils.add_camera_args(parser)
    utils.add_backend_args(parser)

    parser.add_argument(
        "output_dir",
        type=str,
        help="The output folder for your capture",
    )

    args = parser.parse_args()

    led_backend = utils.get_backend(args.backend, args.server)

    os.makedirs(args.output_dir, exist_ok=True)

    reconstructor = Reconstructor(
        args.device,
        args.exposure,
        args.threshold,
        led_backend,
        width=args.width,
        height=args.height,
    )

    while True:

        reconstructor.light()
        reconstructor.open_live_feed()
        cprint("Start scan? [y/n]", Col.PURPLE)

        start_scan = get_user_confirmation()

        reconstructor.close_live_feed()

        if not start_scan:
            break

        reconstructor.dark()

        # The filename is made out of the date, then the resolution of the camera
        string_time = time.strftime("%Y%m%d-%H%M%S")
        filename = f"capture_{string_time}.csv"

        map_data = {}

        total_leds_found = 0

        visible_leds = []

        led_count = led_backend.get_led_count()

        last_camera_motion_check_time = time.time()
        camera_motion_interval_sec = 5

        capture_success = True

        for led_id in tqdm(
            range(led_count),
            unit="LEDs",
            desc=f"Capturing sequence to {filename}",
            total=led_count,
            smoothing=0,
        ):

            result = reconstructor.enable_and_find_led(led_id, debug=True)

            if result:
                visible_leds.append(led_id)
                u, v = result.get_center_normalised()
                map_data[led_id] = {"pos": (u, v)}
                total_leds_found += 1

            is_last = led_id == led_count - 1
            camera_motion_check_overdue = (
                time.time() - last_camera_motion_check_time
            ) > camera_motion_interval_sec

            if camera_motion_check_overdue or is_last:
                camera_motion = reconstructor.get_camera_motion(visible_leds, map_data)
                last_camera_motion_check_time = time.time()

                if camera_motion > 1.0:
                    cprint(
                        f"\nFailed to capture sequence as camera moved by {int(camera_motion)}%",
                        format=Col.FAIL,
                    )
                    capture_success = False
                    break

        if capture_success:
            write_2d_map(os.path.join(args.output_dir, filename), map_data)
            cprint(f"{total_leds_found}/{led_count} leds found", Col.BLUE)
