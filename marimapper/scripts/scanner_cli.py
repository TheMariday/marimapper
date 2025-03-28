import multiprocessing
import argparse
import logging
from marimapper.scripts.arg_tools import (
    parse_common_args,
    add_common_args,
    add_camera_args,
    add_scanner_args,
    add_all_backend_parsers,
)
from marimapper.backends.backend_utils import backend_factories
from marimapper.scanner import Scanner
import os


def main():

    logger = multiprocessing.log_to_stderr()
    logger.setLevel(level=logging.WARNING)

    parser = argparse.ArgumentParser(
        description="Marimapper! Scan LEDs in 3D space using your webcam",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        usage=argparse.SUPPRESS,
    )

    add_common_args(parser)
    add_camera_args(parser)
    add_scanner_args(parser)

    all_backend_parsers = add_all_backend_parsers(parser)

    for backend_parser in all_backend_parsers:
        add_common_args(backend_parser)
        add_camera_args(backend_parser)
        add_scanner_args(backend_parser)

    args = parser.parse_args()

    parse_common_args(args, logger)

    if not os.path.isdir(args.dir):
        raise Exception(f"path {args.dir} does not exist")

    if args.start > args.end:
        raise Exception(f"Start point {args.start} is greater the end point {args.end}")

    backend_factory = backend_factories[args.backend](args)

    scanner = Scanner(
        args.dir,
        args.device,
        args.exposure,
        args.threshold,
        backend_factory,
        args.start,
        args.end,
        args.max_fill,
        args.disable_movement_check,
        60,  # this is the camera fov, it was an argument, but I removed it to reduce clutter
        args.camera_model,
    )

    scanner.mainloop()
    scanner.close()


if __name__ == "__main__":
    main()
