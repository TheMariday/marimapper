import argparse
import sys
sys.path.append('./')
from lib import utils
from lib.color_print import cprint, Col
import time

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Tests a particular backend by making a reference led blink')

    parser.add_argument("--backend", type=str, help="The backend used for led communication",
                        choices=["custom", "fadecandy", "serial", "wled", "lcm"], default="custom")

    parser.add_argument("--reference_led", type=int,
                        help="This is the index of the LED should be visible from the camera", default=0)

    args = parser.parse_args()

    cprint(f"Loading {args.backend} backend")

    led_count = args.reference_led + 1

    try:
        led_backend = utils.get_backend(args.backend, led_count)

        cprint("Press ctrl-c to cancel")

        while True:

            time.sleep(1)

            cprint(f"Turning on LED {args.reference_led}")
            led_backend.set_led(args.reference_led, True)

            time.sleep(1)

            cprint(f"Turning off LED {args.reference_led}")
            led_backend.set_led(args.reference_led, False)

    except NotImplementedError:
        cprint(f"Failed to initialise backend {args.backend}, you need to implement it!", Col.FAIL)
