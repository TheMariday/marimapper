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
        "--input_dir",
        type=str,
        help="Enter the input directory of CSV files",
        required=True,
    )

    args = parser.parse_args()

    maps = get_all_maps(args.input_dir)

    if not maps:
        cprint(f"Failed to load any maps from {args.input_dir}", format=Col.FAIL)
        quit()

    cprint(f"Loaded {len(maps)} maps from {args.input_dir}")

    sfm = SFM(maps)

    success = sfm.process()

    if not success:
        cprint(f"L3D Failed to reconstruct {args.input_dir}", format=Col.FAIL)
        quit()

    sfm.print_points()
    sfm.save_points(Path(args.input_dir) / "reconstruction.csv")
    sfm.display()
