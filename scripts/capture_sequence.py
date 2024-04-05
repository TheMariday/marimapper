import argparse
import os
import sys
import time

import cv2
from tqdm import tqdm

sys.path.append("./")

from lib.reconstructor import Reconstructor
from lib import utils
from lib.map_read_write import write_2d_map
from lib.utils import cprint, Col


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Captures LED flashes to file")

    utils.add_camera_args(parser)
    utils.add_backend_args(parser)

    parser.add_argument(
        "output_dir",
        type=str,
        help="The output folder for your capture",
    )

    parser.add_argument(
        "--led_count", type=int, help="How many LEDs are in your system", required=True
    )

    parser.add_argument(
        "--latency",
        type=int,
        help="The expected latency in ms from an LED being updated to that being updated in the camera",
        default=1000,
    )

    args = parser.parse_args()

    led_backend = utils.get_backend(args.backend, args.led_count, args.server)

    os.makedirs(args.output_dir, exist_ok=True)

    with Reconstructor(
        args.device, args.exposure, args.threshold, width=args.width, height=args.height
    ) as reconstructor:

        while True:

            # The filename is made out of the date, then the resolution of the camera
            string_time = time.strftime("%Y%m%d-%H%M%S")
            filename = f"capture_{string_time}.csv"

            map_data = {}

            total_leds_found = 0

            for led_id in tqdm(
                range(args.led_count),
                unit="LEDs",
                desc=f"Capturing sequence to {filename}",
                total=args.led_count,
                smoothing=0,
            ):

                led_backend.set_led(led_id, True)

                #  wait for LED to turn on
                max_time = time.time() + float(args.latency) / 1000
                result = None
                while result is None and time.time() < max_time:
                    result = reconstructor.find_led(True)

                if result:
                    u, v = result.get_center_normalised()
                    map_data[led_id] = {"pos": (u, v)}
                    total_leds_found += 1

                led_backend.set_led(led_id, False)

                #  wait for LED to turn off
                while reconstructor.find_led() is not None:
                    pass

            write_2d_map(os.path.join(args.output_dir, filename), map_data)

            cv2.destroyWindow("MariMapper")

            cprint(f"{total_leds_found}/{args.led_count} leds found", Col.BLUE)
            cprint("Scan complete, scan again? [y/n]", Col.PURPLE)
            uin = input()
            while uin not in ("y", "n"):
                uin = input()

            if uin == "n":
                break
