import logging

from marimapper.utils import get_marimapper_version
from marimapper.database_populator import camera_models, camera_model_radial
from marimapper.backends.backend_utils import backend_arg_setters

from pathlib import Path
import os
import argparse


def add_camera_args(parser):

    camera_options = parser.add_argument_group("camera options")

    camera_options.add_argument(
        "--device",
        type=int,
        help="Camera device index, set to 1 if using a laptop with a USB webcam",
        default=0,
    )

    camera_options.add_argument(
        "--exposure",
        type=int,
        help="Camera exposure, the lower the value, the darker the image",
        default=-10,
    )
    camera_options.add_argument(
        "--threshold",
        type=int,
        choices=range(0, 255),
        metavar="[0-255]",
        help="LED detection threshold, reducing this number will reduce false positives",
        default=128,
    )


def add_common_args(parser):

    parser.add_argument(
        "-V",
        "--version",
        action="store_true",
        help="Print version and exit",
    )

    parser.add_argument("-v", "--verbose", action="store_true")


def add_scanner_args(parser):

    scanner_options = parser.add_argument_group("scanner options")

    scanner_options.add_argument(
        "dir",
        nargs="?",
        type=Path,
        default=os.getcwd(),
        help="the location for your maps, defaults to the current working directory",
    )

    scanner_options.add_argument(
        "--start", type=int, help="Index of the first led you want to scan", default=0
    )

    scanner_options.add_argument(
        "--end",
        type=int,
        help="Index of the last led you want to scan up to the backends limit",
        default=10000,
    )

    scanner_options.add_argument(
        "--max_fill",
        type=int,
        default=5,
        help="The max number of consecutive LEDs that can be estimated based on adjacent LEDs",
    )

    scanner_options.add_argument(
        "--disable_movement_check",
        action="store_false",
        help="Disables checking of movement when a scan completes",
    )

    scanner_options.add_argument(
        "--camera_model",
        type=str,
        choices=[model.__name__ for model in camera_models],
        default=camera_model_radial.__name__,
        help="Sets the camera model, choose camera_model_opencv_full for higher accuracy",
    )


def parse_common_args(args: argparse.Namespace):
    logger = logging.getLogger()
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    if args.version:
        print(f"Marimapper camera checker, version {get_marimapper_version()}")
        quit()

    if not hasattr(args, "backend"):
        args.backend = "dummy"


def add_all_backend_parsers(parser):
    backend_subparsers = []

    backend_subparser = parser.add_subparsers(help="backend", required=True)

    for backend_name, backend_arg_setter in backend_arg_setters.items():
        backend_parser = backend_subparser.add_parser(backend_name)
        backend_parser.set_defaults(backend=backend_name)
        backend_parser_group = backend_parser.add_argument_group(
            f"{backend_name} options"
        )

        backend_arg_setter(backend_parser_group)

        backend_subparsers.append(backend_parser)

    return backend_subparsers
