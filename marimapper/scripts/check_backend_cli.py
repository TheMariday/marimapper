import argparse
import time
from multiprocessing import log_to_stderr
from marimapper import utils
import logging

logger = log_to_stderr()
logger.setLevel(level=logging.INFO)


def main():

    parser = argparse.ArgumentParser(
        description="Tests a particular backend by making a reference led blink",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    utils.add_backend_args(parser)

    parser.add_argument(
        "--reference_led",
        type=int,
        help="This is the index of the LED should be visible from the camera",
        default=0,
    )

    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    logger.info(f"Loading {args.backend} backend")

    led_backend = utils.get_backend(args.backend, args.server)

    logger.info("Press ctrl-c to cancel")

    while True:
        time.sleep(1)

        logger.info(f"Turning on LED {args.reference_led}")
        led_backend.set_led(args.reference_led, True)

        time.sleep(1)

        logger.info(f"Turning off LED {args.reference_led}")
        led_backend.set_led(args.reference_led, False)


if __name__ == "__main__":
    main()
