import open3d
import numpy as np
import copy
import math
import open3d

def remesh(led_map):

    #pcd = open3d.io.read_point_cloud("D:\\Users\\Sam\\GIT\\L3D\\highbeam.ply")

    pcd = open3d.geometry.PointCloud()

    xyz = [led_map[led_id]["pos"] for led_id in led_map]
    normals = [led_map[led_id]["normal"] for led_id in led_map]

    pcd.points = open3d.utility.Vector3dVector(xyz)
    pcd.normals = open3d.utility.Vector3dVector(normals)

    normals_from_camera = copy.copy(pcd.normals)

    pcd.normals = open3d.utility.Vector3dVector(np.zeros((len(pcd.normals), 3)))

    pcd.estimate_normals() # This needs to be written back to the led map somehow

    assert len(pcd.normals) == len(normals_from_camera)

    for i in range(len(normals_from_camera)):
        normal_from_camera = normals_from_camera[i] / np.linalg.norm(normals_from_camera[i])
        normal_from_estimator = pcd.normals[i] / np.linalg.norm(pcd.normals[i])

        angle = np.arccos(np.clip(np.dot(normal_from_camera, normal_from_estimator), -1.0, 1.0))
        if angle > math.pi/2.0:
            pcd.normals[i] = pcd.normals[i] * -1

    with open3d.utility.VerbosityContextManager(open3d.utility.VerbosityLevel.Debug) as cm:
        rec_mesh, densities = open3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=12)

    rec_mesh = rec_mesh.compute_vertex_normals()
    rec_mesh = rec_mesh.compute_triangle_normals()

    rec_mesh.paint_uniform_color([0.7, 0.7, 0.7])

    return rec_mesh