import click
import sys
import os
import csv
import glob
from marimapper.scripts.basic_photogrammetry_solver import fill_missing_indices


def load_3d_map(filename):
    """Load 3D mapping data from CSV file."""
    data = {}
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data[int(row['index'])] = row
    return data


def scan_2d_indices(data_dir):
    """Scan all 2D detection files in directory."""
    old_cwd = os.getcwd()
    try:
        os.chdir(data_dir)
        files = glob.glob("./led_map_2d_*.csv")
        detection_log = {}

        for fname in files:
            with open(fname, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'index' in row:
                        idx = int(row['index'])
                        if idx not in detection_log:
                            detection_log[idx] = []
                        detection_log[idx].append(os.path.basename(fname))

        return detection_log, files
    finally:
        os.chdir(old_cwd)


def normalize_map_for_csv(final_map):
    """
    Normalize map data for CSV output.
    Converts numpy arrays in pos/norm to individual x,y,z,xn,yn,zn fields.
    Returns dict keyed by index with CSV-ready field values.
    """
    import numpy as np

    normalized = {}
    for idx in sorted(final_map.keys()):
        row_data = final_map[idx]

        # Check if this is the filled format (has 'pos' and 'norm' keys)
        if isinstance(row_data, dict) and 'pos' in row_data:
            pos = row_data['pos']
            norm = row_data['norm']
            error = row_data['error']

            # Convert numpy arrays to floats
            normalized[idx] = {
                'index': idx,
                'x': f"{float(pos[0]):.6f}" if isinstance(pos, np.ndarray) else f"{float(pos[0]):.6f}",
                'y': f"{float(pos[1]):.6f}" if isinstance(pos, np.ndarray) else f"{float(pos[1]):.6f}",
                'z': f"{float(pos[2]):.6f}" if isinstance(pos, np.ndarray) else f"{float(pos[2]):.6f}",
                'xn': f"{float(norm[0]):.6f}" if isinstance(norm, np.ndarray) else f"{float(norm[0]):.6f}",
                'yn': f"{float(norm[1]):.6f}" if isinstance(norm, np.ndarray) else f"{float(norm[1]):.6f}",
                'zn': f"{float(norm[2]):.6f}" if isinstance(norm, np.ndarray) else f"{float(norm[2]):.6f}",
                'error': f"{float(error):.6f}"
            }
        else:
            # Already in CSV format (string fields)
            normalized[idx] = {
                'index': idx,
                **row_data
            }

    return normalized


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
            click.secho(f"Error: {map_file} not found", fg='red', err=True)
            sys.exit(1)

        os.chdir(dir)

        # Load existing 3D map
        try:
            map_data = load_3d_map("led_map_3d.csv")
        except Exception as e:
            click.secho(f"Error loading 3D map: {e}", fg='red', err=True)
            sys.exit(1)

        # Scan 2D detections
        try:
            data_2d_log, files_2d = scan_2d_indices(".")
        except Exception as e:
            click.secho(f"Error scanning 2D files: {e}", fg='red', err=True)
            sys.exit(1)

        all_2d_indices = set(data_2d_log.keys())
        existing_3d_indices = set(map_data.keys())
        missing_indices = sorted(list(all_2d_indices - existing_3d_indices))

        # Report status
        click.secho(f"2D Indices Found: {len(all_2d_indices)} across {len(files_2d)} scans", err=True)
        click.secho(f"3D Indices Mapped: {len(existing_3d_indices)}", err=True)
        click.secho("", err=True)

        if not missing_indices:
            click.secho("Status: COMPLETE", err=True)
            final_map = map_data
        else:
            click.secho(f"Status: INCOMPLETE ({len(missing_indices)} missing)", err=True)
            click.secho("-" * 40, err=True)
            click.secho(f"{'Index':<8} | {'# Views':<8}", err=True)
            click.secho("-" * 40, err=True)
            for idx in missing_indices:
                count = len(data_2d_log[idx])
                click.secho(f"{idx:<8} | {count:<8}", err=True)
            click.secho("-" * 40, err=True)
            click.secho("", err=True)

            if fill:
                # Run photogrammetric reconstruction
                click.secho("Running photogrammetric reconstruction...", err=True)
                click.secho("", err=True)
                final_map = fill_missing_indices(".")
                if final_map is None:
                    click.secho("Error: Photogrammetric reconstruction failed", fg='red', err=True)
                    sys.exit(1)
            else:
                final_map = map_data
                click.secho("(Use --fill to reconstruct missing indices using photogrammetry)", err=True)
                click.secho("", err=True)

        # Output final 3D map to stdout
        if final_map:
            normalized_map = normalize_map_for_csv(final_map)
            fieldnames = ['index', 'x', 'y', 'z', 'xn', 'yn', 'zn', 'error']

            writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
            writer.writeheader()

            for idx in sorted(normalized_map.keys()):
                writer.writerow(normalized_map[idx])

    finally:
        os.chdir(old_cwd)


if __name__ == "__main__":
    main()
