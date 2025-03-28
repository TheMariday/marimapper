import argparse
import time
from multiprocessing import log_to_stderr
import logging
from marimapper.backends.backend_utils import backend_factories
from marimapper.scripts.arg_tools import add_all_backend_parsers
from marimapper.scripts.arg_tools import parse_common_args, add_common_args


def main():
    logger = log_to_stderr()
    logger.setLevel(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="Tests a particular backend by making a reference led blink",
        usage=argparse.SUPPRESS,
    )

    for backend_parser in add_all_backend_parsers(parser, required=True):
        add_common_args(backend_parser)
        backend_parser.add_argument(
            "--reference_led",
            type=int,
            help="This is the index of the LED should be visible from the camera",
            default=0,
        )

    args = parser.parse_args()

    parse_common_args(args, logger)

    logger.info(f"Loading {args.backend} backend")

    backend_factory = backend_factories[args.backend](args)

    led_backend = backend_factory()

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
