import multiprocessing
import argparse
import logging
from marimapper.scripts.launcher import add_scanner_args, add_backend_subparsers

logger = multiprocessing.log_to_stderr()
logger.setLevel(level=logging.WARNING)


def main():
    logger.info("Starting MariMapper")

    parser = argparse.ArgumentParser(
        description="Captures LED flashes to file",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        prog="marimapper",
    )

    add_backend_subparsers(parser)
    add_scanner_args(parser)

    def splash(_):

        print(
            """
        Welcome to Marimapper! Please select a backend from {custom,none,fadecandy,fcmega,pixelblaze,wled}
        For example:
        marimapper fadecandy
        Show help with
        marimapper fadecandy --help
        """
        )

    parser.set_defaults(func=splash)

    args = parser.parse_args()

    args.func(args)


if __name__ == "__main__":
    main()
