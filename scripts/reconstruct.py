import logging
import argparse
import sys
from pathlib import Path

sys.path.append("./")

from lib.sfm.sfm import SFM
from lib.map_read_write import get_all_maps
from lib.utils import cprint, Col

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

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

    args = parser.parse_args()

    maps = get_all_maps(args.input_directory)

    if not maps:
        cprint(f"Failed to load any maps from {args.input_directory}", format=Col.FAIL)
        quit()

    cprint(f"Loaded {len(maps)} maps from {args.input_directory}")

    sfm = SFM(maps)

    success = sfm.process()

    if not success:
        cprint(f"L3D Failed to reconstruct {args.input_directory}", format=Col.FAIL)
        quit()

    sfm.print_points()
    sfm.save_points(Path(args.output_file))
    sfm.display()
