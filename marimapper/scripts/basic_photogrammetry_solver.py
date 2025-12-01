#!/usr/bin/env python3
"""
Marimapper results summary and gap fill script

Uses DLT with Hartley normalization for camera calibration,
RANSAC for outlier rejection, and quality-checked triangulation.
"""

import glob
import sys
import numpy as np
import os
import pandas as pd
import click
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

log = lambda *args, **kwargs: click.secho(*args, err=True, **kwargs)


# --- DATA STRUCTURES ---

@dataclass
class CameraInfo:
    """Stores calibrated camera data with quality metrics."""
    P: np.ndarray                    # 3x4 projection matrix
    points: dict                     # {index: (u, v)}
    filename: str
    reprojection_error: float        # RMS reprojection error
    inlier_count: int                # Number of inliers used
    center: Optional[np.ndarray]     # Camera center in world coords
    azimuth: Optional[float]         # Degrees
    elevation: Optional[float]       # Degrees  
    distance: Optional[float]        # Distance to COM


# --- NORMALIZATION (Critical for DLT stability) ---

def normalize_2d_points(points):
    """
    Hartley normalization for 2D points.
    Translates centroid to origin, scales so RMS distance from origin is sqrt(2).
    
    Returns: (normalized_points, 3x3 transformation matrix T)
    """
    points = np.asarray(points)
    centroid = np.mean(points, axis=0)
    centered = points - centroid
    
    rms_dist = np.sqrt(np.mean(np.sum(centered**2, axis=1)))
    if rms_dist < 1e-10:
        rms_dist = 1.0
    
    scale = np.sqrt(2) / rms_dist
    
    T = np.array([
        [scale, 0, -scale * centroid[0]],
        [0, scale, -scale * centroid[1]],
        [0, 0, 1]
    ])
    
    normalized = centered * scale
    return normalized, T


def normalize_3d_points(points):
    """
    Hartley normalization for 3D points.
    Translates centroid to origin, scales so RMS distance from origin is sqrt(3).
    
    Returns: (normalized_points, 4x4 transformation matrix U)
    """
    points = np.asarray(points)
    centroid = np.mean(points, axis=0)
    centered = points - centroid
    
    rms_dist = np.sqrt(np.mean(np.sum(centered**2, axis=1)))
    if rms_dist < 1e-10:
        rms_dist = 1.0
    
    scale = np.sqrt(3) / rms_dist
    
    U = np.array([
        [scale, 0, 0, -scale * centroid[0]],
        [0, scale, 0, -scale * centroid[1]],
        [0, 0, scale, -scale * centroid[2]],
        [0, 0, 0, 1]
    ])
    
    normalized = centered * scale
    return normalized, U


# --- CAMERA CALIBRATION ---

def compute_projection_matrix_normalized(obj_points, img_points):
    """
    Computes 3x4 projection matrix using DLT with Hartley normalization.
    Much more numerically stable than raw DLT.
    
    Returns: P matrix in original coordinates, or None if failed
    """
    if len(obj_points) < 6:
        return None
    
    obj_points = np.asarray(obj_points)
    img_points = np.asarray(img_points)
    
    # Normalize both point sets
    img_norm, T = normalize_2d_points(img_points)
    obj_norm, U = normalize_3d_points(obj_points)
    
    # Build DLT matrix with normalized coordinates
    A = []
    for i in range(len(obj_points)):
        X, Y, Z = obj_norm[i]
        u, v = img_norm[i]
        A.append([X, Y, Z, 1, 0, 0, 0, 0, -u*X, -u*Y, -u*Z, -u])
        A.append([0, 0, 0, 0, X, Y, Z, 1, -v*X, -v*Y, -v*Z, -v])
    
    A = np.array(A)
    
    try:
        _, S, Vh = np.linalg.svd(A)
        
        # Check conditioning - ratio of largest to smallest singular value
        # If too large, the solution is unreliable
        if S[-1] < 1e-10 or S[0] / S[-1] > 1e10:
            return None
        
        P_norm = Vh[-1].reshape(3, 4)
        
        # Denormalize: P = T^(-1) @ P_norm @ U
        T_inv = np.linalg.inv(T)
        P = T_inv @ P_norm @ U
        
        # Normalize so ||P[2,:3]|| = 1 (makes depth computation consistent)
        scale = np.linalg.norm(P[2, :3])
        if scale < 1e-10:
            return None
        P = P / scale
        
        # Ensure positive depth for the centroid of object points
        centroid_3d = np.mean(obj_points, axis=0)
        depth = P[2] @ np.append(centroid_3d, 1)
        if depth < 0:
            P = -P  # Flip sign to get positive depth
        
        return P
        
    except np.linalg.LinAlgError:
        return None


def compute_reprojection_error(P, obj_points, img_points):
    """
    Compute RMS reprojection error for a projection matrix.
    
    Returns: (rms_error, individual_errors)
    """
    obj_points = np.asarray(obj_points)
    img_points = np.asarray(img_points)
    
    errors = []
    for obj, img in zip(obj_points, img_points):
        proj = P @ np.append(obj, 1)
        if abs(proj[2]) < 1e-10:
            errors.append(float('inf'))
            continue
        
        proj_2d = proj[:2] / proj[2]
        error = np.linalg.norm(proj_2d - img)
        errors.append(error)
    
    errors = np.array(errors)
    rms = np.sqrt(np.mean(errors**2))
    return rms, errors


def calibrate_camera_ransac(obj_points, img_points, 
                            n_iterations=500, 
                            inlier_threshold=5.0,
                            min_inliers=8):
    """
    RANSAC-based camera calibration for robustness to outliers.
    
    Args:
        obj_points: List of 3D points
        img_points: List of corresponding 2D points
        n_iterations: Number of RANSAC iterations
        inlier_threshold: Max reprojection error (pixels) to be considered inlier
        min_inliers: Minimum inliers required for valid model
    
    Returns: (best_P, inlier_mask) or (None, None)
    """
    obj_points = np.asarray(obj_points)
    img_points = np.asarray(img_points)
    n_points = len(obj_points)
    
    if n_points < 6:
        return None, None
    
    best_P = None
    best_inliers = None
    best_inlier_count = 0
    
    # Minimum sample size for DLT
    sample_size = 6
    
    for _ in range(n_iterations):
        # Random sample
        indices = np.random.choice(n_points, sample_size, replace=False)
        
        P = compute_projection_matrix_normalized(
            obj_points[indices], 
            img_points[indices]
        )
        
        if P is None:
            continue
        
        # Evaluate on all points
        _, errors = compute_reprojection_error(P, obj_points, img_points)
        inliers = errors < inlier_threshold
        inlier_count = np.sum(inliers)
        
        if inlier_count > best_inlier_count:
            best_inlier_count = inlier_count
            best_inliers = inliers
            best_P = P
    
    if best_inlier_count < min_inliers:
        return None, None
    
    # Refine using all inliers
    refined_P = compute_projection_matrix_normalized(
        obj_points[best_inliers],
        img_points[best_inliers]
    )
    
    if refined_P is not None:
        return refined_P, best_inliers
    
    return best_P, best_inliers


# --- CAMERA POSE EXTRACTION ---

def extract_camera_info(P, com):
    """
    Extract camera position and orientation relative to subject COM.
    
    Returns: (azimuth_deg, elevation_deg, distance, camera_center)
    """
    try:
        M = P[:, :3]
        p4 = P[:, 3]
        
        # Camera center: C = -M^(-1) * p4
        det = np.linalg.det(M)
        if abs(det) < 1e-10:
            return None, None, None, None
        
        M_inv = np.linalg.inv(M)
        C = -M_inv @ p4
        
        # Vector from subject COM to camera
        cam_rel = C - com
        distance = np.linalg.norm(cam_rel)
        
        if distance < 1e-6:
            return None, None, None, C
        
        cam_dir = cam_rel / distance
        
        # Azimuth: angle in XY plane from +Y axis
        azimuth = np.degrees(np.arctan2(cam_dir[0], cam_dir[1]))
        
        # Elevation: angle from horizontal (positive = up)
        elevation = np.degrees(np.arcsin(np.clip(cam_dir[2], -1, 1)))
        
        return azimuth, elevation, distance, C
        
    except Exception:
        return None, None, None, None


# --- TRIANGULATION WITH FALLBACKS ---

def triangulate_point_dlt(cameras, detections):
    """
    Triangulates a single 3D point using DLT (SVD-based).
    
    Returns: 3D point or None
    """
    if len(cameras) < 2:
        return None
    
    A = []
    for P, (u, v) in zip(cameras, detections):
        A.append(u * P[2] - P[0])
        A.append(v * P[2] - P[1])
    
    A = np.array(A)
    
    try:
        _, S, Vh = np.linalg.svd(A)
        
        # Check if solution is well-conditioned
        if S[-1] < 1e-10:
            return None
        
        X_homogeneous = Vh[-1]
        
        if abs(X_homogeneous[3]) < 1e-10:
            return None
        
        X_cartesian = X_homogeneous[:3] / X_homogeneous[3]
        return X_cartesian
        
    except np.linalg.LinAlgError:
        return None


def compute_reprojection_errors(point_3d, cameras, detections):
    """Compute reprojection errors for a 3D point across all views."""
    errors = []
    depths = []
    for P, (u, v) in zip(cameras, detections):
        proj = P @ np.append(point_3d, 1)
        depths.append(proj[2])
        if abs(proj[2]) < 1e-10:
            errors.append(float('inf'))
        else:
            proj_2d = proj[:2] / proj[2]
            errors.append(np.linalg.norm(proj_2d - np.array([u, v])))
    return errors, depths


def compute_ray_angle(point_3d, cam_infos):
    """Compute maximum angle between camera rays to a 3D point."""
    centers = [c.center for c in cam_infos if c.center is not None]
    if len(centers) < 2:
        return 180.0  # Assume good if we can't compute
    
    rays = []
    for c in centers:
        ray = point_3d - c
        norm = np.linalg.norm(ray)
        if norm > 1e-6:
            rays.append(ray / norm)
    
    if len(rays) < 2:
        return 180.0
    
    max_angle = 0
    for i in range(len(rays)):
        for j in range(i + 1, len(rays)):
            cos_angle = np.clip(np.dot(rays[i], rays[j]), -1, 1)
            angle = np.degrees(np.arccos(cos_angle))
            max_angle = max(max_angle, angle)
    
    return max_angle


def backproject_with_depth_estimate(cam_info, detection, reference_depth):
    """
    Back-project a 2D point using estimated depth from nearby known points.
    
    This is a fallback when triangulation fails - uses single view + depth guess.
    Less accurate but always produces a result.
    
    Args:
        cam_info: CameraInfo with projection matrix P
        detection: (u, v) pixel coordinates
        reference_depth: Estimated depth from known nearby points
    
    Returns: 3D point estimate
    """
    P = cam_info.P
    u, v = detection
    
    # P = [M | p4], we need to invert the projection
    # For a point at depth d along the ray: X = C + d * ray_direction
    M = P[:, :3]
    p4 = P[:, 3]
    
    try:
        M_inv = np.linalg.inv(M)
        C = -M_inv @ p4  # Camera center
        
        # Ray direction: M^(-1) @ [u, v, 1]^T (unnormalized)
        ray = M_inv @ np.array([u, v, 1])
        ray_norm = np.linalg.norm(ray)
        if ray_norm < 1e-10:
            return None
        ray = ray / ray_norm
        
        # Project along ray to estimated depth
        point_3d = C + reference_depth * ray
        return point_3d
        
    except np.linalg.LinAlgError:
        return None


@dataclass
class TriangulationResult:
    """Result of triangulation attempt with metadata."""
    point: Optional[np.ndarray]
    method: str
    quality: float  # Lower is better, -1 for interpolated
    num_views: int
    confidence: str  # "high", "medium", "low", "fallback"


def triangulate_with_fallbacks(idx, cameras, detections, cam_infos, 
                                known_data, com,
                                strict_reproj=10.0,
                                relaxed_reproj=50.0,
                                strict_ray_angle=2.0,
                                relaxed_ray_angle=0.5):
    """
    Triangulate a point with cascading fallback strategies.
    
    Cascade order:
    1. Strict triangulation (tight reprojection + ray angle thresholds)
    2. Relaxed triangulation (looser thresholds)
    3. Best-effort triangulation (any result with positive depth)
    4. Single-view backprojection with depth estimate
    5. Linear interpolation (always succeeds)
    
    Returns: TriangulationResult (always contains a valid point)
    """
    num_views = len(cameras)
    
    # === TIER 1: Strict quality triangulation ===
    if num_views >= 2:
        point_3d = triangulate_point_dlt(cameras, detections)
        
        if point_3d is not None:
            errors, depths = compute_reprojection_errors(point_3d, cameras, detections)
            ray_angle = compute_ray_angle(point_3d, cam_infos)
            
            all_positive_depth = all(d > 0 for d in depths)
            max_error = max(errors)
            mean_error = np.mean(errors)
            
            # Tier 1: Strict thresholds
            if all_positive_depth and max_error < strict_reproj and ray_angle > strict_ray_angle:
                return TriangulationResult(
                    point=point_3d,
                    method="Triangulated (strict)",
                    quality=mean_error,
                    num_views=num_views,
                    confidence="high"
                )
            
            # === TIER 2: Relaxed thresholds ===
            if all_positive_depth and max_error < relaxed_reproj and ray_angle > relaxed_ray_angle:
                return TriangulationResult(
                    point=point_3d,
                    method="Triangulated (relaxed)",
                    quality=mean_error,
                    num_views=num_views,
                    confidence="medium"
                )
            
            # === TIER 3: Best-effort (just need positive depth and bounded error) ===
            if all_positive_depth and max_error < 200.0:
                return TriangulationResult(
                    point=point_3d,
                    method="Triangulated (best-effort)",
                    quality=mean_error,
                    num_views=num_views,
                    confidence="low"
                )
            
            # Check if flipping helps (camera behind subject issue)
            if not all_positive_depth:
                point_flipped = -point_3d
                errors_f, depths_f = compute_reprojection_errors(point_flipped, cameras, detections)
                if all(d > 0 for d in depths_f) and max(errors_f) < relaxed_reproj:
                    return TriangulationResult(
                        point=point_flipped,
                        method="Triangulated (flipped)",
                        quality=np.mean(errors_f),
                        num_views=num_views,
                        confidence="low"
                    )
    
    # === TIER 4: Single-view backprojection ===
    if num_views >= 1:
        # Estimate depth from nearby known points
        nearby_depths = []
        for known_idx, data in known_data.items():
            if abs(known_idx - idx) <= 10:  # Within 10 indices
                # Compute depth of known point from first camera
                P = cam_infos[0].P
                proj = P @ np.append(data['pos'], 1)
                if proj[2] > 0:
                    nearby_depths.append(proj[2])
        
        if not nearby_depths:
            # Use distance to COM as fallback depth estimate
            if cam_infos[0].distance is not None:
                reference_depth = cam_infos[0].distance
            else:
                reference_depth = np.linalg.norm(com)
        else:
            reference_depth = np.median(nearby_depths)
        
        # Try backprojection from camera with best view
        for cam, det in zip(cam_infos, detections):
            point_3d = backproject_with_depth_estimate(cam, det, reference_depth)
            if point_3d is not None:
                # Sanity check: point should be reasonably close to known points
                distances_to_known = [np.linalg.norm(point_3d - known_data[k]['pos']) 
                                      for k in known_data.keys()]
                if min(distances_to_known) < reference_depth * 2:  # Within 2x expected range
                    return TriangulationResult(
                        point=point_3d,
                        method="Backprojected",
                        quality=-1.0,
                        num_views=1,
                        confidence="low"
                    )
    
    # === TIER 5: Linear interpolation (always succeeds) ===
    interp_pos, _ = interpolate_linear(idx, known_data)
    
    return TriangulationResult(
        point=interp_pos,
        method="Interpolated",
        quality=-1.0,
        num_views=0,
        confidence="fallback"
    )


# --- STANDARD LOADERS ---

def load_3d_map(filename):
    """Load 3D map from CSV."""
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
    """Load all 2D detection files."""
    files = sorted(glob.glob("./led_map_2d_*.csv"))
    views = []
    
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
    if idx in keys:
        return known_data[idx]['pos'], known_data[idx]['norm']
    
    prev_k = next((k for k in reversed(keys) if k < idx), None)
    next_k = next((k for k in keys if k > idx), None)
    
    pos = np.array([0., 0., 0.])
    norm = np.array([0., 0., 1.])
    
    if prev_k is not None and next_k is not None:
        alpha = (idx - prev_k) / (next_k - prev_k)
        p1, n1 = known_data[prev_k]['pos'], known_data[prev_k]['norm']
        p2, n2 = known_data[next_k]['pos'], known_data[next_k]['norm']
        pos = (1 - alpha) * p1 + alpha * p2
        norm = (1 - alpha) * n1 + alpha * n2
    elif prev_k is not None:
        pos, norm = known_data[prev_k]['pos'], known_data[prev_k]['norm']
    elif next_k is not None:
        pos, norm = known_data[next_k]['pos'], known_data[next_k]['norm']
    
    norm_len = np.linalg.norm(norm)
    if norm_len > 1e-9:
        norm = norm / norm_len
    
    return pos, norm


# --- MAIN EXECUTION ---

def fill_missing_indices(data_dir=".", 
                         ransac_iterations=500,
                         ransac_threshold=5.0,
                         min_calibration_points=8,
                         triangulation_reproj_threshold=10.0,
                         min_ray_angle=2.0):
    """
    Fills in missing LED indices using photogrammetric reconstruction.
    
    Improvements over basic implementation:
    - Hartley normalization for numerical stability
    - RANSAC for outlier rejection during camera calibration  
    - Quality-checked triangulation with ray angle validation
    - Reprojection error reporting
    
    Args:
        data_dir: Directory containing led_map_3d.csv and led_map_2d_*.csv
        ransac_iterations: Number of RANSAC iterations for camera calibration
        ransac_threshold: Reprojection error threshold (pixels) for RANSAC inliers
        min_calibration_points: Minimum points needed for camera calibration
        triangulation_reproj_threshold: Max reprojection error for triangulated points
        min_ray_angle: Minimum angle (degrees) between rays for valid triangulation
    
    Returns:
        dict: Final map with all indices, or None if processing failed
    """
    old_cwd = os.getcwd()
    try:
        os.chdir(data_dir)
        
        # 1. Load Data
        map_3d = load_3d_map("led_map_3d.csv")
        views = load_all_2d_files()
        
        if not views:
            log("Error: No 2D view files found.", fg='red')
            return None
        
        # Compute center of mass
        positions = np.array([map_3d[idx]['pos'] for idx in sorted(map_3d.keys())])
        com = np.mean(positions, axis=0)
        
        log(f"Loaded {len(map_3d)} known 3D points, COM at [{com[0]:.2f}, {com[1]:.2f}, {com[2]:.2f}]")
        log(f"Found {len(views)} 2D view files\n")
        
        # 2. Calibrate cameras with RANSAC
        log(f"Step 1: Camera calibration (RANSAC, {ransac_iterations} iterations, {ransac_threshold}px threshold)")
        log("-" * 80)
        
        calibrated_cameras = []
        
        for view in views:
            common_indices = set(view['points'].keys()).intersection(set(map_3d.keys()))
            
            if len(common_indices) < min_calibration_points:
                log(f"  {Path(view['filename']).name}: SKIPPED ({len(common_indices)} pts < {min_calibration_points} required)")
                continue
            
            obj_pts = np.array([map_3d[idx]['pos'] for idx in common_indices])
            img_pts = np.array([view['points'][idx] for idx in common_indices])
            
            P, inlier_mask = calibrate_camera_ransac(
                obj_pts, img_pts,
                n_iterations=ransac_iterations,
                inlier_threshold=ransac_threshold,
                min_inliers=min_calibration_points
            )
            
            if P is None:
                log(f"  {Path(view['filename']).name}: FAILED (RANSAC found no good model)")
                continue
            
            # Compute final reprojection error on inliers
            inlier_obj = obj_pts[inlier_mask]
            inlier_img = img_pts[inlier_mask]
            rms_error, _ = compute_reprojection_error(P, inlier_obj, inlier_img)
            
            # Extract camera pose
            azimuth, elevation, distance, center = extract_camera_info(P, com)
            
            cam_info = CameraInfo(
                P=P,
                points=view['points'],
                filename=view['filename'],
                reprojection_error=rms_error,
                inlier_count=int(np.sum(inlier_mask)),
                center=center,
                azimuth=azimuth,
                elevation=elevation,
                distance=distance
            )
            calibrated_cameras.append(cam_info)
            
            # Log result
            timestamp = Path(view['filename']).stem.split('_')[-1]
            pose_str = ""
            if azimuth is not None:
                pose_str = f"az={azimuth:+6.1f}° el={elevation:+5.1f}° d={distance:.2f}"
            
            log(f"  {timestamp}: {cam_info.inlier_count}/{len(common_indices)} inliers, "
                f"RMS={rms_error:.2f}px, {pose_str}")
        
        log(f"\nStep 2: Calibrated {len(calibrated_cameras)}/{len(views)} cameras\n")
        
        if len(calibrated_cameras) < 2:
            log("Error: Need at least 2 calibrated cameras for triangulation.", fg='red')
            return None
        
        # 3. Identify missing indices
        all_2d_indices = set()
        for v in views:
            all_2d_indices.update(v['points'].keys())
        
        missing_indices = sorted(list(all_2d_indices - set(map_3d.keys())))
        log(f"Step 3: Reconstructing {len(missing_indices)} missing points")
        log("-" * 80)
        
        final_map = map_3d.copy()
        
        # Track outcomes by confidence level
        stats = {
            'high': 0,
            'medium': 0,
            'low': 0,
            'fallback': 0
        }
        method_counts = {}
        reconstruction_table = []
        
        for idx in missing_indices:
            # Gather cameras that see this point
            participating_cams = []
            participating_detections = []
            participating_infos = []
            
            for cam in calibrated_cameras:
                if idx in cam.points:
                    participating_cams.append(cam.P)
                    participating_detections.append(cam.points[idx])
                    participating_infos.append(cam)
            
            # Use cascading fallback system
            result = triangulate_with_fallbacks(
                idx=idx,
                cameras=participating_cams,
                detections=participating_detections,
                cam_infos=participating_infos,
                known_data=final_map,
                com=com,
                strict_reproj=triangulation_reproj_threshold,
                relaxed_reproj=triangulation_reproj_threshold * 5,
                strict_ray_angle=min_ray_angle,
                relaxed_ray_angle=min_ray_angle / 4
            )
            
            # Track statistics
            stats[result.confidence] += 1
            method_counts[result.method] = method_counts.get(result.method, 0) + 1
            
            # Get interpolated normal (triangulation doesn't give us surface normals)
            _, interp_norm = interpolate_linear(idx, final_map)
            
            # Store result
            final_map[idx] = {
                'pos': result.point,
                'norm': interp_norm,
                'error': result.quality if result.quality >= 0 else -1.0
            }
            
            pos_str = f"[{result.point[0]:.4f}, {result.point[1]:.4f}, {result.point[2]:.4f}]"
            quality_str = f"{result.quality:.2f}" if result.quality >= 0 else "N/A"
            reconstruction_table.append([
                idx, result.method, result.num_views, 
                result.confidence, quality_str, pos_str
            ])
        
        # Print reconstruction table
        if reconstruction_table:
            df_table = pd.DataFrame(
                reconstruction_table, 
                columns=["Index", "Method", "Views", "Confidence", "Quality", "Position"]
            )
            log(df_table.to_string(index=False) + "\n")
        
        # Summary
        log("Reconstruction Summary by Confidence:")
        log(f"  High (strict triangulation):    {stats['high']}")
        log(f"  Medium (relaxed triangulation): {stats['medium']}")
        log(f"  Low (best-effort/backproject):  {stats['low']}")
        log(f"  Fallback (interpolated):        {stats['fallback']}")
        log(f"  Total points in final map:      {len(final_map)}")
        log("")
        log("Methods used:")
        for method, count in sorted(method_counts.items(), key=lambda x: -x[1]):
            log(f"  {method}: {count}")
        log("")
        
        return final_map
        
    finally:
        os.chdir(old_cwd)


@click.command()
@click.option('--dir', '-d', default='.', help='Data directory')
@click.option('--ransac-iter', default=500, help='RANSAC iterations')
@click.option('--ransac-thresh', default=5.0, help='RANSAC inlier threshold (pixels)')
@click.option('--min-points', default=8, help='Min calibration points per camera')
@click.option('--reproj-thresh', default=10.0, help='Max reprojection error for triangulation')
@click.option('--min-angle', default=2.0, help='Min ray angle (degrees) for triangulation')
def main(dir, ransac_iter, ransac_thresh, min_points, reproj_thresh, min_angle):
    """Fill missing LED indices using photogrammetric reconstruction."""
    
    final_map = fill_missing_indices(
        data_dir=dir,
        ransac_iterations=ransac_iter,
        ransac_threshold=ransac_thresh,
        min_calibration_points=min_points,
        triangulation_reproj_threshold=reproj_thresh,
        min_ray_angle=min_angle
    )
    
    if final_map is None:
        sys.exit(1)
    
    # Output CSV to stdout
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