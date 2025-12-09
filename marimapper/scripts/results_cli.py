import argparse
import sys
import os
import glob
import csv


def log(msg, **kwargs):
    sys.stderr.write(str(msg) + "\n")


def scan_2d_indices(data_dir):
    """Scan all 2D detection files in directory."""
    search_pattern = os.path.join(data_dir, "led_map_2d_*.csv")
    files = glob.glob(search_pattern)
    detection_log = {}

    for fname in files:
        with open(fname, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                idx = int(row["index"])
                if idx not in detection_log:
                    detection_log[idx] = []
                detection_log[idx].append(os.path.basename(fname))

    return detection_log, files


def main():
    parser = argparse.ArgumentParser(
        description="Summarize LED mapping results.\n\nShows mapping status (2D detections vs 3D calibration).\nOutputs final 3D mapping as CSV to stdout (all logging goes to stderr).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--dir",
        "-d",
        default=".",
        help="Directory containing led_map_3d.csv and led_map_2d_*.csv files (default: current directory)",
    )

    args = parser.parse_args()

    # Validate directory
    if not os.path.isdir(args.dir):
        log(f"Error: Directory '{args.dir}' does not exist.")
        sys.exit(1)

    # Check if required files exist
    map_file_path = os.path.join(args.dir, "led_map_3d.csv")
    if not os.path.exists(map_file_path):
        log(f"Error: {map_file_path} not found")
        sys.exit(1)

    # Load existing 3D map
    existing_3d_indices = set()
    map_rows = []
    map_fieldnames = []

    with open(map_file_path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        map_fieldnames = reader.fieldnames
        for row in reader:
            map_rows.append(row)
            existing_3d_indices.add(int(row["index"]))

    # Scan 2D detections
    data_2d_log, files_2d = scan_2d_indices(args.dir)
    all_2d_indices = set(data_2d_log.keys())

    # Infer expected total from max index found in either 2D or 3D data
    if not all_2d_indices and not existing_3d_indices:
        max_index = -1
    else:
        max_val_2d = max(all_2d_indices) if all_2d_indices else -1
        max_val_3d = max(existing_3d_indices) if existing_3d_indices else -1
        max_index = max(max_val_2d, max_val_3d)

    expected_indices = set(range(max_index + 1))
    missing_indices = sorted(list(expected_indices - existing_3d_indices))

    # Report status
    log(f"2D Indices Found: {len(all_2d_indices)} across {len(files_2d)} scans")
    log(f"Expected Total: {len(expected_indices)} (indices 0-{max_index})")
    log(f"Total 3D Indices Mapped: {len(existing_3d_indices)}\n")

    if not missing_indices:
        log("Status: COMPLETE")
    else:
        log(f"Status: INCOMPLETE ({len(missing_indices)} missing)")
        log("(Try --interpolation_max_error and --interpolation_max_fill)\n")

        # Display missing indices table
        idx_width, view_width = len("Index"), len("# Views")
        rows = [(idx, len(data_2d_log.get(idx, []))) for idx in missing_indices]
        log(f"{'Index':<{idx_width}}  {'# Views':>{view_width}}")
        for idx, count in rows:
            log(f"{idx:<{idx_width}}  {count:>{view_width}}")
        log("")

    # Output final 3D mapping as CSV to stdout
    writer = csv.DictWriter(sys.stdout, fieldnames=map_fieldnames)
    writer.writeheader()
    writer.writerows(map_rows)


if __name__ == "__main__":
    main()
