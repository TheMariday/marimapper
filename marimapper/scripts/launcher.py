import argparse
from marimapper.utils import get_marimapper_version
from functools import partial
import logging
from marimapper.scanner import Scanner
import os

from marimapper.database_populator import camera_models, camera_model_radial

from pathlib import Path

logger = logging.getLogger()


def add_common_args(parser):
    parser.add_argument(
        "--device",
        type=int,
        help="Camera device index, set to 1 if using a laptop with a USB webcam",
        default=0,
    )

    parser.add_argument(
        "--exposure",
        type=int,
        help="Camera exposure, the lower the value, the darker the image",
        default=-10,
    )
    parser.add_argument(
        "--threshold",
        type=int,
        choices=range(0, 255),
        metavar="[0-255]",
        help="LED detection threshold, reducing this number will reduce false positives",
        default=128,
    )

    parser.add_argument(
        "-V",
        "--version",
        action="store_true",
        help="Print version and exit",
    )

    parser.add_argument("-v", "--verbose", action="store_true")


def add_scanner_args(parser):
    add_common_args(parser)

    parser.add_argument(
        "--start", type=int, help="Index of the first led you want to scan", default=0
    )

    parser.add_argument(
        "--end",
        type=int,
        help="Index of the last led you want to scan up to the backends limit",
        default=10000,
    )
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

    parser.add_argument(
        "--disable_movement_check",
        action="store_false",
        help="Disables checking of movement when a scan completes",
    )

    parser.add_argument(
        "--camera_model",
        type=str,
        choices=[model.__name__ for model in camera_models],
        default=camera_model_radial.__name__,
        help="Sets the camera model, choose camera_model_opencv_full for higher accuracy",
    )

    parser.add_argument(
        "--camera_fov",
        type=int,
        default=60,
        help="The initial camera field of view in degrees, change this if your camera FOV is wildly different",
    )


def launch_scanner(args: argparse.Namespace, backend_factory: partial):
    if args.version:
        print(f"Marimapper, version {get_marimapper_version()}")
        quit()

    if not os.path.isdir(args.dir):
        raise Exception(f"path {args.dir} does not exist")

    if args.start > args.end:
        raise Exception(f"Start point {args.start} is greater the end point {args.end}")

    if args.verbose:
        logger.setLevel(logging.DEBUG)

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
        args.camera_fov,
        args.camera_model,
    )

    scanner.mainloop()
    scanner.close()


def launch_custom(args: argparse.Namespace):
    from marimapper.backends.custom.custom_backend import custom_backend_factory

    backend_factory = custom_backend_factory(args)
    launch_scanner(args, backend_factory)


def launch_dummy(args: argparse.Namespace):
    from marimapper.backends.dummy.dummy_backend import dummy_backend_factory

    backend_factory = dummy_backend_factory()
    launch_scanner(args, backend_factory)


def launch_fadecandy(args: argparse.Namespace):
    from marimapper.backends.fadecandy.fadecandy_backend import (
        fadecandy_backend_factory,
    )

    backend_factory = fadecandy_backend_factory(args)
    launch_scanner(args, backend_factory)


def launch_fcmega(args: argparse.Namespace):
    from marimapper.backends.fcmega.fcmega_backend import fcmega_backend_factory

    backend_factory = fcmega_backend_factory()
    launch_scanner(args, backend_factory)


def launch_pixelblaze(args: argparse.Namespace):
    from marimapper.backends.pixelblaze.pixelblaze_backend import (
        pixelblaze_backend_factory,
    )

    backend_factory = pixelblaze_backend_factory(args)
    launch_scanner(args, backend_factory)


def launch_wled(args: argparse.Namespace):
    from marimapper.backends.wled.wled_backend import wled_backend_factory

    backend_factory = wled_backend_factory(args)
    launch_scanner(args, backend_factory)


def add_backend_subparsers(parser):
    from marimapper.backends.custom.custom_backend import custom_backend_set_args
    from marimapper.backends.dummy.dummy_backend import dummy_backend_set_args
    from marimapper.backends.fadecandy.fadecandy_backend import (
        fadecandy_backend_set_args,
    )
    from marimapper.backends.fcmega.fcmega_backend import fcmega_backend_set_args
    from marimapper.backends.pixelblaze.pixelblaze_backend import (
        pixelblaze_backend_set_args,
    )
    from marimapper.backends.wled.wled_backend import wled_backend_set_args

    backend_config = [
        ["custom", custom_backend_set_args, launch_custom],
        ["none", dummy_backend_set_args, launch_dummy],
        ["fadecandy", fadecandy_backend_set_args, launch_fadecandy],
        ["fcmega", fcmega_backend_set_args, launch_fcmega],
        ["pixelblaze", pixelblaze_backend_set_args, launch_pixelblaze],
        ["wled", wled_backend_set_args, launch_wled],
    ]

    backend_subparser = parser.add_subparsers(help="backend")

    for backend_name, backend_arg_setter, backend_launcher in backend_config:
        backend_parser = backend_subparser.add_parser(backend_name)
        backend_parser.set_defaults(func=backend_launcher)
        add_scanner_args(backend_parser)
        backend_arg_setter(backend_parser)
