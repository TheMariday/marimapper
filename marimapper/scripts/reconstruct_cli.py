# DO NOT MOVE THIS, see the same import in scanner.py
from marimapper.sfm_process import add_normals

import argparse
import logging
import multiprocessing
import os
from pathlib import Path

from marimapper.file_tools import get_all_2d_led_maps, write_3d_leds_to_file
from marimapper.led import LED2D, LED3D, fill_gaps, get_view_ids, recenter, rescale
from marimapper.scripts.arg_tools import (
    add_common_args,
    add_reconstruction_args,
    parse_common_args,
)
from marimapper.sfm import sfm
from marimapper.database_populator import camera_models, camera_model_radial


def reconstruct(
    leds_2d: list[LED2D],
    interpolation_max_fill: int = 5,
    interpolation_max_error: float = 0.2,
    camera_model_name: str = camera_model_radial.__name__,
    camera_fov: int = 60,
) -> list[LED3D]:
    """Builds the 3D map from 2D maps, the same way the scanner does while it captures"""

    camera_model = next(m for m in camera_models if m.__name__ == camera_model_name)

    leds_3d = sfm(leds_2d, camera_model=camera_model, camera_fov=camera_fov)

    if len(leds_3d) > 0:
        rescale(leds_3d)

        fill_gaps(
            leds_3d,
            min_distance=1 - interpolation_max_error,
            max_distance=1 + interpolation_max_error,
            max_missing=interpolation_max_fill,
        )

        recenter(leds_3d)

        add_normals(leds_3d)

    return leds_3d


def main():

    logger = multiprocessing.log_to_stderr()
    logger.setLevel(level=logging.WARNING)

    parser = argparse.ArgumentParser(
        description="Builds the 3D map from the 2D scans saved by marimapper, e.g. after "
        "marimapper --capture_only",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        usage=argparse.SUPPRESS,
    )

    add_common_args(parser)
    parser.add_argument(
        "--dir",
        type=Path,
        default=os.getcwd(),
        help="the folder with your 2D scans, the 3D map is written there too, defaults to the current working directory",
    )
    add_reconstruction_args(parser)

    args = parser.parse_args()

    parse_common_args(args, logger)

    if not os.path.isdir(args.dir):
        raise Exception(f"path {args.dir} does not exist")

    leds_2d = get_all_2d_led_maps(args.dir)
    views = get_view_ids(leds_2d)

    if len(views) < 2:
        raise Exception(
            f"Found {len(views)} scan(s) in {args.dir}, at least 2 views are needed to build a 3D map"
        )

    print(f"Reconstructing from {len(views)} views, this can take a moment...")

    leds_3d = reconstruct(
        leds_2d,
        args.interpolation_max_fill if args.interpolation_max_fill != -1 else 10000,
        args.interpolation_max_error if args.interpolation_max_error != -1 else 10000,
        args.camera_model,
    )

    if len(leds_3d) == 0:
        raise Exception(
            "The reconstruction found no LEDs, the scans probably don't overlap enough"
        )

    output_file = Path(args.dir, "led_map_3d.csv")
    write_3d_leds_to_file(leds_3d, output_file)

    print(f"Reconstructed {len(leds_3d)} LEDs, saved to {output_file}")


if __name__ == "__main__":
    main()
