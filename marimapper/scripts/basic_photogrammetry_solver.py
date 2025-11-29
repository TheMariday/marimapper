import glob
import sys
import numpy as np
import os
import pandas as pd
import click
from pathlib import Path

log = lambda *args, **kwargs: click.secho(*args, err=True, **kwargs)


def extract_camera_info(P, com):
    """
    Extract camera position and orientation relative to subject COM.

    Args:
        P: 3x4 projection matrix
        com: 3D center of mass of the LED points

    Returns:
        (azimuth_deg, elevation_deg, distance)
        - azimuth: angle in XY plane around Z axis (degrees, 0=+Y, 90=+X, etc.)
        - elevation: angle down from horizontal (degrees, 0=horiz, -90=down, 90=up)
        - distance: 3D distance from COM to camera
    """
    try:
        M = P[:, :3]
        p4 = P[:, 3]

        # Extract camera center: C = -M^(-1) * p4
        M_inv = np.linalg.inv(M)
        C = -M_inv @ p4

        # Vector from subject COM to camera
        cam_rel = C - com
        distance = np.linalg.norm(cam_rel)

        if distance < 1e-6:
            return None, None, None

        # Normalize direction vector
        cam_dir = cam_rel / distance

        # Azimuth: angle in XY plane (assuming Z is up)
        # atan2(x, y) gives angle from Y axis, 0 = +Y, 90 = +X
        azimuth = np.degrees(np.arctan2(cam_dir[0], cam_dir[1]))

        # Elevation: angle below horizontal plane
        # 0 = horizontal, -90 = straight down, 90 = straight up
        elevation = -np.degrees(np.arcsin(np.clip(cam_dir[2], -1, 1)))

        return azimuth, elevation, distance
    except Exception:
        return None, None, None


# --- MATHS HELPERS ---

def compute_projection_matrix(obj_points, img_points):
    """
    Computes the 3x4 Camera Projection Matrix (P) using Direct Linear Transform (DLT).
    Maps 3D world coords -> 2D image coords.
    Requires at least 6 common points.
    """
    if len(obj_points) < 6:
        return None

    # Construct the DLT matrix A
    A = []
    for i in range(len(obj_points)):
        X, Y, Z = obj_points[i]
        u, v = img_points[i]
        # Two equations per point
        A.append([X, Y, Z, 1, 0, 0, 0, 0, -u*X, -u*Y, -u*Z, -u])
        A.append([0, 0, 0, 0, X, Y, Z, 1, -v*X, -v*Y, -v*Z, -v])
    
    A = np.array(A)
    # Solve A*p = 0 using SVD
    U, S, Vh = np.linalg.svd(A)
    L = Vh[-1] # The last row of Vh is the solution
    
    # Reshape into 3x4 projection matrix
    P = L.reshape(3, 4)
    return P

def triangulate_point(cameras, detections):
    """
    Triangulates a single 3D point given n cameras and n 2D detections.
    cameras: list of 3x4 Projection Matrices
    detections: list of (u, v) tuples
    """
    if len(cameras) < 2:
        return None # Need at least 2 views to intersect rays

    # Construct system A*X = 0
    A = []
    for P, (u, v) in zip(cameras, detections):
        # P[0], P[1], P[2] are the rows of P
        # u * P_2 * X = P_0 * X  =>  (u*P_2 - P_0) * X = 0
        A.append(u * P[2] - P[0])
        # v * P_2 * X = P_1 * X  =>  (v*P_2 - P_1) * X = 0
        A.append(v * P[2] - P[1])
        
    A = np.array(A)
    
    # Solve using SVD
    U, S, Vh = np.linalg.svd(A)
    X_homogeneous = Vh[-1]
    
    # Convert from Homogeneous (X,Y,Z,W) to Cartesian (X/W, Y/W, Z/W)
    X_cartesian = X_homogeneous[:3] / X_homogeneous[3]
    return X_cartesian

# --- STANDARD LOADERS ---

def load_3d_map(filename):
    """Load 3D map from CSV using pandas."""
    if not os.path.exists(filename):
        log(f"Error: {filename} not found.", fg='red')
        sys.exit(1)

    df = pd.read_csv(filename)
    data = {}
    for _, row in df.iterrows():
        idx = int(row['index'])
        data[idx] = {
            'pos': np.array([float(row['x']), float(row['y']), float(row['z'])]),
            'norm': np.array([float(row['xn']), float(row['yn']), float(row['zn'])]),
            'error': float(row['error'])
        }
    return data

def load_all_2d_files():
    """Load all 2D detection files using pandas."""
    files = glob.glob("./led_map_2d_*.csv")
    views = []  # List of dicts: [{'filename': str, 'points': {index: (u,v)}}]

    for fname in files:
        df = pd.read_csv(fname)
        view_data = {}
        for _, row in df.iterrows():
            idx = int(row['index'])
            view_data[idx] = (float(row['u']), float(row['v']))
        views.append({'filename': fname, 'points': view_data})

    return views

def interpolate_linear(idx, known_data):
    """Fallback: Linear interpolation for normals or failed triangulation."""
    keys = sorted(known_data.keys())
    if idx in keys: return known_data[idx]['pos'], known_data[idx]['norm']

    prev_k = next((k for k in reversed(keys) if k < idx), None)
    next_k = next((k for k in keys if k > idx), None)

    pos, norm = np.array([0.,0.,0.]), np.array([0.,0.,1.])
    
    if prev_k is not None and next_k is not None:
        alpha = (idx - prev_k) / (next_k - prev_k)
        p1, n1 = known_data[prev_k]['pos'], known_data[prev_k]['norm']
        p2, n2 = known_data[next_k]['pos'], known_data[next_k]['norm']
        pos = (1-alpha)*p1 + alpha*p2
        norm = (1-alpha)*n1 + alpha*n2
    elif prev_k is not None:
        pos, norm = known_data[prev_k]['pos'], known_data[prev_k]['norm']
    elif next_k is not None:
        pos, norm = known_data[next_k]['pos'], known_data[next_k]['norm']
        
    return pos, norm / (np.linalg.norm(norm) + 1e-9)

# --- MAIN EXECUTION ---

def fill_missing_indices(data_dir="."):
    """
    Fills in missing LED indices using photogrammetric reconstruction.

    Uses DLT (Direct Linear Transform) to estimate camera projection matrices
    from known calibration points, then SVD-based triangulation to reconstruct
    missing 3D positions. Falls back to linear interpolation for points with
    insufficient view coverage.

    Args:
        data_dir: Directory containing led_map_3d.csv and led_map_2d_*.csv files

    Returns:
        dict: Final map with all indices, or None if processing failed
    """
    import os
    old_cwd = os.getcwd()
    try:
        os.chdir(data_dir)

        # 1. Load Data
        map_3d = load_3d_map("led_map_3d.csv")
        views = load_all_2d_files()

        # Compute center of mass of 3D points (subject position)
        positions = np.array([map_3d[idx]['pos'] for idx in sorted(map_3d.keys())])
        com = np.mean(positions, axis=0)

        # 2. Estimate Cameras (Projection Matrices using DLT + SVD)
        # We define a "Camera" for each 2D file
        valid_cameras = []

        log(f"Step 1: Estimating camera poses using DLT for {len(views)} views...")

        for view in views:
            # Find common points between this 2D view and the known 3D map
            common_indices = set(view['points'].keys()).intersection(set(map_3d.keys()))

            if len(common_indices) < 8: # DLT needs 6, but 8+ is safer for noise
                log(f"  Skipped {view['filename']}: only {len(common_indices)} common points (need 8+)")
                continue

            obj_pts = []
            img_pts = []
            for idx in common_indices:
                obj_pts.append(map_3d[idx]['pos'])
                img_pts.append(view['points'][idx])

            P = compute_projection_matrix(obj_pts, img_pts)
            if P is not None:
                valid_cameras.append({
                    'P': P,
                    'points': view['points'],
                    'filename': view['filename']
                })

                # Extract timestamp from filename (e.g., "led_map_2d_20251128-133730.csv" -> "20251128-133730")
                timestamp = Path(view['filename']).stem.split('_')[-1]

                # Extract camera position relative to subject COM
                azimuth, elevation, distance = extract_camera_info(P, com)
                if azimuth is not None:
                    info_str = f"azim={azimuth:+7.1f}° elev={elevation:+6.1f}° dist={distance:6.2f}"
                    log(f"  {timestamp}: {len(common_indices)} pts, {info_str}")
                else:
                    log(f"  {timestamp}: {len(common_indices)} points")

        log(f"Step 2: Successfully calibrated {len(valid_cameras)} / {len(views)} views using DLT\n")

        # 3. Identify Missing Pixels
        # We want to check ranges. Let's assume the max index in 2D files is the strip length
        all_2d_indices = set()
        for v in views:
            all_2d_indices.update(v['points'].keys())

        missing_indices = sorted(list(all_2d_indices - set(map_3d.keys())))

        log(f"Step 3: Reconstructing {len(missing_indices)} missing pixels using SVD triangulation\n")

        final_map = map_3d.copy()

        # Track reconstruction outcomes
        triangulated_count = 0
        interpolated_insufficient_count = 0
        interpolated_failed_count = 0
        reconstruction_table = []

        for idx in missing_indices:
            # Gather all cameras that saw this missing index
            participating_cameras = []
            participating_detections = []

            for cam in valid_cameras:
                if idx in cam['points']:
                    participating_cameras.append(cam['P'])
                    participating_detections.append(cam['points'][idx])

            method = "FAILED"
            result_pos = None

            # Try Triangulation first (SVD-based)
            if len(participating_cameras) >= 2:
                result_pos = triangulate_point(participating_cameras, participating_detections)
                if result_pos is not None:
                    method = "Triangulated (SVD)"
                    triangulated_count += 1
                else:
                    # Triangulation failed despite having enough views
                    method = "Interpolated (SVD failed)"
                    interpolated_failed_count += 1
                    result_pos, _ = interpolate_linear(idx, final_map)
            else:
                # Not enough views for triangulation
                method = "Interpolated (insufficient)"
                interpolated_insufficient_count += 1
                result_pos, _ = interpolate_linear(idx, final_map)

            # For normals, triangulation doesn't help us (cameras don't see orientation easily).
            # We assume standard linear flow for normals.
            _, interp_norm = interpolate_linear(idx, final_map)

            # Add to map
            final_map[idx] = {
                'pos': result_pos,
                'norm': interp_norm,
                'error': -1.0 if "Interpolated" in method else 0.001
            }

            pos_str = f"[{result_pos[0]:.6f}, {result_pos[1]:.6f}, {result_pos[2]:.6f}]"
            reconstruction_table.append([idx, method, len(participating_cameras), pos_str])

        # Print reconstruction table using pandas
        if reconstruction_table:
            df_table = pd.DataFrame(reconstruction_table, columns=["Index", "Method", "Views", "3D Position"])
            log(df_table.to_string(index=False) + "\n")

        # Print summary
        log("Reconstruction Summary:")
        log(f"  Triangulated (SVD):          {triangulated_count}")
        log(f"  Interpolated (insufficient): {interpolated_insufficient_count}")
        log(f"  Interpolated (SVD failed):   {interpolated_failed_count}")
        log(f"  Total pixels in final map:   {len(final_map)}\n")

        return final_map

    finally:
        os.chdir(old_cwd)


def main():
    final_map = fill_missing_indices(".")
    if final_map is None:
        sys.exit(1)

    # 4. Output to stdout using pandas
    rows = []
    for idx in sorted(final_map.keys()):
        d = final_map[idx]
        rows.append({
            'index': idx,
            'x': f"{d['pos'][0]:.6f}",
            'y': f"{d['pos'][1]:.6f}",
            'z': f"{d['pos'][2]:.6f}",
            'xn': f"{d['norm'][0]:.6f}",
            'yn': f"{d['norm'][1]:.6f}",
            'zn': f"{d['norm'][2]:.6f}",
            'error': f"{d['error']:.6f}"
        })

    df = pd.DataFrame(rows)
    df.to_csv(sys.stdout, index=False)

if __name__ == "__main__":
    main()