from marimapper.scanner import Scanner
from multiprocessing import log_to_stderr
import os
import argparse
import logging
from marimapper.utils import add_camera_args, add_backend_args
from pathlib import Path

logger = log_to_stderr()
logger.setLevel(level=logging.ERROR)


def main():
    logger.info("Starting MariMapper")

    parser = argparse.ArgumentParser(
        description="Captures LED flashes to file",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    add_camera_args(parser)
    add_backend_args(parser)

    parser.add_argument("-v", "--verbose", action="store_true")

    parser.add_argument(
        "dir",
        nargs="?",
        type=Path,
        default=os.getcwd(),
        help="the location for your maps, defaults to the current working directory",
    )

    parser.add_argument(
        "--max_fill",
        type=int,
        default=5,
        help="The max number of consecutive LEDs that can be estimated based on adjacent LEDs",
    )

    args = parser.parse_args()

    if not os.path.isdir(args.dir):
        raise Exception(f"path {args.dir} does not exist")

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    scanner = Scanner(
        args.dir,
        args.device,
        args.exposure,
        args.threshold,
        args.backend,
        args.server,
        args.start,
        args.end,
        args.max_fill,
    )

    scanner.mainloop()
    scanner.close()


if __name__ == "__main__":
    main()
