import numpy as np
import math
import open3d


def fix_normals(led_map):

    pcd = open3d.geometry.PointCloud()

    led_ids = list(led_map.keys())

    xyz = [led_map[led_id]["pos"] for led_id in led_ids]
    normals_from_camera = [led_map[led_id]["normal"] for led_id in led_ids]

    pcd.points = open3d.utility.Vector3dVector(xyz)

    pcd.normals = open3d.utility.Vector3dVector(np.zeros((len(pcd.normals), 3)))

    pcd.estimate_normals()  # This needs to be written back to the led map somehow

    assert len(pcd.normals) == len(normals_from_camera)

    for i in range(len(normals_from_camera)):
        normal_from_camera = normals_from_camera[i] / np.linalg.norm(normals_from_camera[i])
        normal_from_estimator = pcd.normals[i] / np.linalg.norm(pcd.normals[i])

        angle = np.arccos(np.clip(np.dot(normal_from_camera, normal_from_estimator), -1.0, 1.0))

        led_map[led_ids[i]]["normal"] = pcd.normals[i] * (-1 if angle > math.pi / 2.0 else 1)

    return led_map

def remesh(led_map, mesh_detail=12):

    pcd = open3d.geometry.PointCloud()

    pcd.points = open3d.utility.Vector3dVector([led_map[led_id]["pos"] for led_id in led_map])
    pcd.normals = open3d.utility.Vector3dVector([led_map[led_id]["normal"] for led_id in led_map])

    with open3d.utility.VerbosityContextManager(open3d.utility.VerbosityLevel.Debug) as cm:
        rec_mesh, densities = open3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=12)

    rec_mesh = rec_mesh.compute_vertex_normals()
    rec_mesh = rec_mesh.compute_triangle_normals()

    rec_mesh.paint_uniform_color([0.7, 0.7, 0.7])

    return rec_mesh

def save_mesh(mesh, filename):
    open3d.io.write_triangle_mesh(filename, mesh)