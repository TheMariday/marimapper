import logging
import argparse
import os

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description='Reconstructs 3D information from LED flashes captured with capture_sequence.py')

    parser.add_argument("--input_dir", type=str,
                        help="Enter the input directory of CSV files", required=True)

    args = parser.parse_args()

    output_dir_full = os.path.join(os.getcwd(), args.input_dir)

    print(output_dir_full)

    filenames = os.listdir(output_dir_full)

    resolution = None

    points = []

    for filename in filenames:

        filepath = os.path.join(os.getcwd(), args.input_dir, filename)

        # Check resolution

        file_resolution = [int(r) for r in filename.replace(".csv","").split("_")[-2:]]  # don't ask
        if resolution is None:
            resolution = file_resolution

        if file_resolution != file_resolution:
            logging.error(f"Failed to load file {filename} as resolution does not match other resolutions in this file")


        logging.info(f"Loading file {filepath} with resolution {file_resolution}")

        with open(filepath, "r") as file:
            lines = file.readlines()
            file_points = [[int(v) for v in l.strip().split(",")] for l in lines]  # I really need to go to bed

            points.append(file_points)


    # Do my own custom SFM stuff here