import click
import sys
import os
import glob
import pandas as pd


def log(*args, **kwargs):
    click.secho(*args, err=True, **kwargs)


def scan_2d_indices(data_dir):
    """Scan all 2D detection files in directory."""
    old_cwd = os.getcwd()
    try:
        os.chdir(data_dir)
        files = glob.glob("./led_map_2d_*.csv")
        detection_log = {}

        for fname in files:
            df = pd.read_csv(fname)
            for _, row in df.iterrows():
                idx = int(row["index"])
                if idx not in detection_log:
                    detection_log[idx] = []
                detection_log[idx].append(os.path.basename(fname))

        return detection_log, files
    finally:
        os.chdir(old_cwd)


@click.command()
@click.option(
    "--dir",
    "-d",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Directory containing led_map_3d.csv and led_map_2d_*.csv files (default: current directory)",
)
def main(dir):
    """
    Summarize LED mapping results.

    Shows mapping status (2D detections vs 3D calibration).

    Outputs final 3D mapping as CSV to stdout (all logging goes to stderr).
    """
    old_cwd = os.getcwd()
    try:
        # Check if required files exist
        map_file = os.path.join(dir, "led_map_3d.csv")
        if not os.path.exists(map_file):
            log(f"Error: {map_file} not found", fg="red")
            sys.exit(1)

        os.chdir(dir)

        # Load existing 3D map
        try:
            map_df = pd.read_csv("led_map_3d.csv")
        except Exception as e:
            log(f"Error loading 3D map: {e}", fg="red")
            sys.exit(1)

        # Scan 2D detections
        try:
            data_2d_log, files_2d = scan_2d_indices(".")
        except Exception as e:
            log(f"Error scanning 2D files: {e}", fg="red")
            sys.exit(1)

        all_2d_indices = set(data_2d_log.keys())
        existing_3d_indices = set(map_df["index"].astype(int))
        missing_indices = sorted(list(all_2d_indices - existing_3d_indices))

        # Report status
        log(f"2D Indices Found: {len(all_2d_indices)} across {len(files_2d)} scans")
        log(f"3D Indices Mapped: {len(existing_3d_indices)}\n")

        if not missing_indices:
            log("Status: COMPLETE")
        else:
            log(f"Status: INCOMPLETE ({len(missing_indices)} missing)")
            log(f"Try --interpolation_max_error and --interpolation_max_fill")

            # Display missing indices table using pandas
            missing_table_data = [
                [idx, len(data_2d_log[idx])] for idx in missing_indices
            ]
            df_missing = pd.DataFrame(missing_table_data, columns=["Index", "# Views"])
            log(df_missing.to_string(index=False) + "\n")

        map_df.to_csv(sys.stdout, index=False)

    finally:
        os.chdir(old_cwd)


if __name__ == "__main__":
    main()
