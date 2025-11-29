import glob
import csv
import sys
import numpy as np
import os

# --- MATH HELPERS (The "Not Naive" Part) ---

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
    data = {}
    if not os.path.exists(filename):
        sys.stderr.write(f"Error: {filename} not found.\n")
        sys.exit(1)
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            idx = int(row['index'])
            data[idx] = {
                'pos': np.array([float(row['x']), float(row['y']), float(row['z'])]),
                'norm': np.array([float(row['xn']), float(row['yn']), float(row['zn'])]),
                'error': float(row['error'])
            }
    return data

def load_all_2d_files():
    files = glob.glob("./led_map_2d_*.csv")
    views = [] # List of dicts: [{'filename': str, 'points': {index: (u,v)}}]
    
    for fname in files:
        view_data = {}
        with open(fname, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                idx = int(row['index'])
                # Assuming detections are floats
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

def main():
    # 1. Load Data
    map_3d = load_3d_map("led_map_3d.csv")
    views = load_all_2d_files()
    
    # 2. Estimate Cameras (Projection Matrices)
    # We define a "Camera" for each 2D file
    valid_cameras = []
    
    sys.stderr.write(f"Calculating camera poses for {len(views)} views...\n")
    
    for view in views:
        # Find common points between this 2D view and the known 3D map
        common_indices = set(view['points'].keys()).intersection(set(map_3d.keys()))
        
        if len(common_indices) < 8: # DLT needs 6, but 8+ is safer for noise
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

    sys.stderr.write(f"Successfully calibrated {len(valid_cameras)} / {len(views)} views.\n")

    # 3. Identify Missing Pixels
    # We want to check ranges. Let's assume the max index in 2D files is the strip length
    all_2d_indices = set()
    for v in views:
        all_2d_indices.update(v['points'].keys())
    
    missing_indices = sorted(list(all_2d_indices - set(map_3d.keys())))
    
    sys.stderr.write(f"Attempting to reconstruct {len(missing_indices)} missing pixels.\n")
    sys.stderr.write("-" * 60 + "\n")
    sys.stderr.write(f"{'Index':<6} | {'Method':<15} | {'Views used':<10} | {'Result'}\n")
    sys.stderr.write("-" * 60 + "\n")

    final_map = map_3d.copy()

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
        
        # Try Triangulation first
        if len(participating_cameras) >= 2:
            result_pos = triangulate_point(participating_cameras, participating_detections)
            if result_pos is not None:
                method = "Triangulated"
        
        # Fallback to Interpolation if Triangulation failed or not enough views
        if result_pos is None:
            method = "Interpolated"
            result_pos, _ = interpolate_linear(idx, final_map)
            
        # For normals, triangulation doesn't help us (cameras don't see orientation easily).
        # We assume standard linear flow for normals.
        _, interp_norm = interpolate_linear(idx, final_map)
        
        # Add to map
        final_map[idx] = {
            'pos': result_pos,
            'norm': interp_norm,
            'error': -1.0 if method == "Interpolated" else 0.001
        }
        
        sys.stderr.write(f"{idx:<6} | {method:<15} | {len(participating_cameras):<10} | {result_pos}\n")

    # 4. Output
    fieldnames = ['index', 'x', 'y', 'z', 'xn', 'yn', 'zn', 'error']
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
    writer.writeheader()
    
    for idx in sorted(final_map.keys()):
        d = final_map[idx]
        writer.writerow({
            'index': idx,
            'x': f"{d['pos'][0]:.6f}",
            'y': f"{d['pos'][1]:.6f}",
            'z': f"{d['pos'][2]:.6f}",
            'xn': f"{d['norm'][0]:.6f}",
            'yn': f"{d['norm'][1]:.6f}",
            'zn': f"{d['norm'][2]:.6f}",
            'error': f"{d['error']:.6f}"
        })

if __name__ == "__main__":
    main()