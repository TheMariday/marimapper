import argparse
import os
import sys
import time
from tqdm import tqdm
from pathlib import Path

sys.path.append("./")

from lib.reconstructor import Reconstructor
from lib import utils
from lib.utils import cprint, Col, get_user_confirmation
from lib.led_map_2d import LEDMap2D
from lib.sfm.sfm import SFM
from lib.visualize_model import Renderer3D


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

    sfm = SFM(Path(args.output_dir), rescale=True, interpolate=True)
    sfm.start()

    renderer3d = Renderer3D(Path(args.output_dir) / "led_map_3d.csv")
    renderer3d.start()

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

        filepath = os.path.join(args.output_dir, f"led_map_2d_{string_time}.csv")

        led_map_2d = LEDMap2D()

        total_leds_found = 0

        visible_leds = []

        led_count = led_backend.get_led_count()

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

            result = reconstructor.enable_and_find_led(led_id, debug=True)

            if result:
                visible_leds.append(led_id)
                led_map_2d.add_detection(led_id, result)
                total_leds_found += 1

            is_last = led_id == led_count - 1
            camera_motion_check_overdue = (
                time.time() - last_camera_motion_check_time
            ) > camera_motion_interval_sec

            if camera_motion_check_overdue or is_last:
                camera_motion = reconstructor.get_camera_motion(
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

    sfm.shutdown()
    renderer3d.shutdown()
    sfm.join()
    renderer3d.join()
