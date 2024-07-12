import argparse
import sys
import csv

sys.path.append("./")

from lib import utils


def read_coordinates_from_csv(csv_file_name):
    print(f"Loading coordinates from {csv_file_name}")
    with open(csv_file_name, newline="") as csvfile:
        csv_reader = csv.DictReader(csvfile)
        list_of_leds = []
        for row in csv_reader:
            list_of_leds.append(row)

        # Find the largest index in the list
        num_leds = int(max(list_of_leds, key=list_of_leds.index)["index"])

        final_coordinate_list = []

        for i in range(num_leds):
            # Either find the list with the matching index
            # or default to [0,0,0] if we never saw the pixel
            coords = next(
                (item for item in list_of_leds if int(item["index"]) == i),
                {"x": 0, "y": 0, "z": 0},
            )
            final_coordinate_list.append(
                [float(coords["x"]), float(coords["y"]), float(coords["z"])]
            )

        return final_coordinate_list


def main_function(cli_args):
    final_coordinate_list = read_coordinates_from_csv(cli_args.csv_file)
    print(final_coordinate_list)

    upload_coordinates = utils.get_user_confirmation(
        "Upload coordinates to Pixelblaze? [y/n]: "
    )
    if not upload_coordinates:
        return

    print(f"Uploading coordinates to pixelblaze {cli_args.server}")
    led_backend = utils.get_backend("pixelblaze", cli_args.server)
    led_backend.set_map_coordinates(final_coordinate_list)
    print("Finished")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload led_map_3d.csv to pixelblaze")
    parser.add_argument("--server", type=str, help="pixelblaze server ip")
    parser.add_argument(
        "--csv_file",
        type=str,
        help="The csv file to convert",
        default="my_scan/led_map_3d.csv",
    )
    args = parser.parse_args()

    main_function(args)
