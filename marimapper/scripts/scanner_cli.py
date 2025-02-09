from marimapper.scanner import Scanner
import multiprocessing
import os
import argparse
import logging
from marimapper.utils import add_common_args, add_backend_args, get_marimapper_version
from pathlib import Path

logger = multiprocessing.log_to_stderr()
logger.setLevel(level=logging.WARNING)


def main():
    logger.info("Starting MariMapper")

    parser = argparse.ArgumentParser(
        description="Captures LED flashes to file",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    add_common_args(parser)
    add_backend_args(parser)

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
        "--fast",
        action="store_true",
        help="Runs marimapper in fast mode",
    )

    args = parser.parse_args()

    if args.version:
        print(f"Marimapper, version {get_marimapper_version()}")
        quit()

    if not os.path.isdir(args.dir):
        raise Exception(f"path {args.dir} does not exist")

    if args.start > args.end:
        raise Exception(f"Start point {args.start} is greater the end point {args.end}")

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # This is to do with an issue with open3d bug in estimate normals
    # https://github.com/isl-org/Open3D/issues/1428
    # if left to its default fork start method, add_normals in sfm_process will fail
    # add_normals is also in the wrong file, it should be in sfm.py, but this causes a dependancy crash
    # I think there is something very wrong with open3d.geometry.PointCloud.estimate_normals()
    # See https://github.com/TheMariday/marimapper/issues/46
    # I would prefer not to call this here as it means that any process being called after this will have a different
    # spawn method, however it makes tests more robust in isolation
    # This is only an issue on Linux, as on Windows and Mac, the default start method is spawn
    multiprocessing.set_start_method("spawn")

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
        args.disable_movement_check,
        args.fast,
    )

    scanner.mainloop()
    scanner.close()


if __name__ == "__main__":
    main()
