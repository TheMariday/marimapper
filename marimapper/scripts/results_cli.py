import click
import sys
import os
import glob
import pandas as pd
from marimapper.scripts.basic_photogrammetry_solver import fill_missing_indices

log = lambda *args, **kwargs: click.secho(*args, err=True, **kwargs)

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
                idx = int(row['index'])
                if idx not in detection_log:
                    detection_log[idx] = []
                detection_log[idx].append(os.path.basename(fname))

        return detection_log, files
    finally:
        os.chdir(old_cwd)


def normalize_map_for_csv(final_map):
    """Convert final map data to pandas DataFrame for CSV output."""
    rows = []
    for idx in sorted(final_map.keys()):
        row_data = final_map[idx]

        # Handle filled format (numpy arrays) and CSV format (strings)
        if isinstance(row_data, dict) and 'pos' in row_data:
            pos = row_data['pos']
            norm = row_data['norm']
            error = row_data['error']
            rows.append({
                'index': idx,
                'x': f"{float(pos[0]):.6f}",
                'y': f"{float(pos[1]):.6f}",
                'z': f"{float(pos[2]):.6f}",
                'xn': f"{float(norm[0]):.6f}",
                'yn': f"{float(norm[1]):.6f}",
                'zn': f"{float(norm[2]):.6f}",
                'error': f"{float(error):.6f}"
            })
        else:
            # Already in CSV format
            rows.append({'index': idx, **row_data})

    return pd.DataFrame(rows)


@click.command()
@click.option(
    '--dir',
    default='.',
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help='Directory containing led_map_3d.csv and led_map_2d_*.csv files (default: current directory)'
)
@click.option(
    '--fill',
    is_flag=True,
    help='Fill in missing LED indices using photogrammetric reconstruction (DLT + SVD)'
)
def main(dir, fill):
    """
    Process LED mapping results.

    Shows mapping status (2D detections vs 3D calibration). When --fill is used,
    reconstructs missing 3D positions using photogrammetric methods.

    Outputs final 3D mapping as CSV to stdout (all logging goes to stderr).
    """
    old_cwd = os.getcwd()
    try:
        # Check if required files exist
        map_file = os.path.join(dir, "led_map_3d.csv")
        if not os.path.exists(map_file):
            log(f"Error: {map_file} not found", fg='red')
            sys.exit(1)

        os.chdir(dir)

        # Load existing 3D map
        try:
            map_df = pd.read_csv("led_map_3d.csv")
            map_data = {int(idx): row.to_dict() for idx, row in map_df.iterrows()}
        except Exception as e:
            log(f"Error loading 3D map: {e}", fg='red')
            sys.exit(1)

        # Scan 2D detections
        try:
            data_2d_log, files_2d = scan_2d_indices(".")
        except Exception as e:
            log(f"Error scanning 2D files: {e}", fg='red')
            sys.exit(1)

        all_2d_indices = set(data_2d_log.keys())
        existing_3d_indices = set(map_data.keys())
        missing_indices = sorted(list(all_2d_indices - existing_3d_indices))

        # Report status
        log(f"2D Indices Found: {len(all_2d_indices)} across {len(files_2d)} scans")
        log(f"3D Indices Mapped: {len(existing_3d_indices)}\n")

        if not missing_indices:
            log("Status: COMPLETE")
            final_map = map_data
        else:
            log(f"Status: INCOMPLETE ({len(missing_indices)} missing)")

            # Display missing indices table using pandas
            missing_table_data = [[idx, len(data_2d_log[idx])] for idx in missing_indices]
            df_missing = pd.DataFrame(missing_table_data, columns=["Index", "# Views"])
            log(df_missing.to_string(index=False) + "\n")

            if fill:
                # Run photogrammetric reconstruction
                log("Running photogrammetric reconstruction...\n")
                final_map = fill_missing_indices(".")
                if final_map is None:
                    log("Error: Photogrammetric reconstruction failed", fg='red')
                    sys.exit(1)
            else:
                final_map = map_data
                log("(Use --fill to reconstruct missing indices using photogrammetry)\n")

        # Output final 3D map to stdout using pandas
        if final_map:
            df_output = normalize_map_for_csv(final_map)
            df_output.to_csv(sys.stdout, index=False)

    finally:
        os.chdir(old_cwd)


if __name__ == "__main__":
    main()
