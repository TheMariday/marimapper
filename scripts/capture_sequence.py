import argparse
import os
import sys
import time

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

    first_scan = True

    while True:

        reconstructor.light()
        reconstructor.open_live_feed()
        cprint(f"Start scan{'' if first_scan else ' again'}? [y/n]", Col.PURPLE)
        uin = input()
        while uin not in ("y", "n"):
            uin = input()

        reconstructor.close_live_feed()

        if uin == "n":
            break

        first_scan = False
        reconstructor.dark()

        # The filename is made out of the date, then the resolution of the camera
        string_time = time.strftime("%Y%m%d-%H%M%S")
        filename = f"capture_{string_time}.csv"

        map_data = {}

        total_leds_found = 0

        led_count = led_backend.get_led_count()

        for led_id in tqdm(
            range(led_count),
            unit="LEDs",
            desc=f"Capturing sequence to {filename}",
            total=led_count,
            smoothing=0,
        ):

            result = reconstructor.enable_and_find_led(led_id, debug=True)

            if result:
                u, v = result.get_center_normalised()
                map_data[led_id] = {"pos": (u, v)}
                total_leds_found += 1

        write_2d_map(os.path.join(args.output_dir, filename), map_data)

        cprint(f"{total_leds_found}/{led_count} leds found", Col.BLUE)
