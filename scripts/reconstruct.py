import argparse
import sys
from pathlib import Path

sys.path.append("./")

from lib.sfm.sfm import SFM
from lib.utils import cprint, Col
from lib.led_map_2d import get_all_2d_led_maps
from lib.visualize_model import Renderer3D

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

    sfm = SFM(Path(args.input_directory))

    success = sfm.process(
        rescale=(not args.no_rescale), interpolate=(not args.no_interpolation)
    )

    if not success:
        cprint(
            f"MariMapper Failed to reconstruct {args.input_directory}", format=Col.FAIL
        )
        quit()

    r3d = Renderer3D(Path(args.output_file))
    r3d.run()
