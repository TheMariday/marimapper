import logging
import argparse
import sys
sys.path.append("./")

from lib.sfm.sfm import SFM

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

    sfm = SFM(args.input_dir)

    sfm.process()

    sfm.print_points()
    sfm.save_points("points3d.csv")
    sfm.display()