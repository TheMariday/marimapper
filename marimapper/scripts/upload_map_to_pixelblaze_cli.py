import argparse
from marimapper.backends.pixelblaze.upload_map_to_pixelblaze import (
    upload_map_to_pixelblaze,
)


def main():
    parser = argparse.ArgumentParser(
        description="Upload led_map_3d.csv to pixelblaze",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--server", type=str, help="pixelblaze server ip")
    parser.add_argument(
        "--csv_file", type=str,
        help="The led_map_3d.csv map file to upload",
        default="led_map_3d.csv",
    )
    args = parser.parse_args()

    upload_map_to_pixelblaze(args)


if __name__ == "__main__":
    main()
