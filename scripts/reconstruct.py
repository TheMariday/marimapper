import argparse
import sys
from pathlib import Path

sys.path.append("./")

from lib.sfm.sfm import SFM
from lib.utils import cprint, Col
from lib.led_map_2d import get_all_2d_led_maps

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Reconstructs 3D information from LED flashes captured with 9_point_box.py"
    )

    parser.add_argument(
        "input_directory",
        type=str,
        help="Enter the input directory of CSV files",
    )

    parser.add_argument(
        "--output_file",
        type=str,
        help="Enter the output filepath for the csv",
        default="reconstruction.csv",
    )

    parser.add_argument(
        "--no_rescale", help="Use this to disable rescaling", action="store_true"
    )

    parser.add_argument(
        "--no_interpolation",
        help="Use this to disable led interpolation",
        action="store_true",
    )

    args = parser.parse_args()

    maps = get_all_2d_led_maps(args.input_directory)

    if not maps:
        cprint(f"Failed to load any maps from {args.input_directory}", format=Col.FAIL)
        quit()

    cprint(f"Loaded {len(maps)} maps from {args.input_directory}")

    sfm = SFM(maps)

    success = sfm.process(
        rescale=(not args.no_rescale), interpolate=(not args.no_interpolation)
    )

    if not success:
        cprint(
            f"MariMapper Failed to reconstruct {args.input_directory}", format=Col.FAIL
        )
        quit()

    sfm.save_points(Path(args.output_file))
    sfm.display()
