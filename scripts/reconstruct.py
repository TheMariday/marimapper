import logging
import argparse
import sys
from pathlib import Path

sys.path.append("./")

from lib.sfm.sfm import SFM
from lib.map_read_write import get_all_maps

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="Reconstructs 3D information from LED flashes captured with capture_sequence.py"
    )

    parser.add_argument(
        "--input_dir",
        type=str,
        help="Enter the input directory of CSV files",
        required=True,
    )

    args = parser.parse_args()

    maps = get_all_maps(args.input_dir)

    sfm = SFM(maps)

    sfm.process()

    sfm.print_points()
    sfm.save_points(Path(args.input_dir) / "reconstruction.csv")
    sfm.display()
