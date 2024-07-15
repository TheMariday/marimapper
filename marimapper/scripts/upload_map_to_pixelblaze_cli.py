import argparse
from marimapper.backends.pixelblaze.upload_map_to_pixelblaze import (
    upload_map_to_pixelblaze,
)


def main():
    parser = argparse.ArgumentParser(description="Upload led_map_3d.csv to pixelblaze")
    parser.add_argument("--server", type=str, help="pixelblaze server ip")
    parser.add_argument(
        "--csv_file", type=str, help="The csv file to convert", required=True
    )
    args = parser.parse_args()

    upload_map_to_pixelblaze(args)


if __name__ == "__main__":
    main()
