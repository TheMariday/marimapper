import open3d
import numpy as np


def render_model(model):

    __vis = open3d.visualization.Visualizer()
    __vis.create_window()

    cam_geometry = []
    for K, R, t, width, height in model.cams:
        cam_geometry.extend(draw_camera(K, R, t, width, height))

    for c in cam_geometry:
        __vis.add_geometry(c)

    arrow = open3d.geometry.TriangleMesh.create_coordinate_frame(
        size=0.6, origin=[0, 0, 0]
    )
    __vis.add_geometry(arrow)

    pcd = open3d.geometry.PointCloud()

    xyz = [model.points[led_id]["pos"] for led_id in model.points]
    rgb = [[0, 0, 0] for _ in model.points]

    pcd.points = open3d.utility.Vector3dVector(xyz)
    pcd.colors = open3d.utility.Vector3dVector(rgb)

    __vis.add_geometry(pcd)
    __vis.poll_events()
    __vis.update_renderer()

    __vis.poll_events()
    __vis.update_renderer()

    view_ctl = __vis.get_view_control()
    view_ctl.set_up((0, 1, 0))
    view_ctl.set_lookat((0, 0, 0))
    view_ctl.set_zoom(0.3)

    __vis.run()
    __vis.destroy_window()


def draw_camera(K, R, t, w, h):
    """Create axis, plane and pyramed geometries in Open3D format.
    :param K: calibration matrix (camera intrinsics)
    :param R: rotation matrix
    :param t: translation
    :param w: image width
    :param h: image height
    :return: camera model geometries (axis, plane and pyramid)
    """

    scale = 1
    color = [0.8, 0.2, 0.8]

    # intrinsics
    K = K.copy()
    Kinv = np.linalg.inv(K)

    # 4x4 transformation
    T = np.column_stack((R, t))
    T = np.vstack((T, (0, 0, 0, 1)))

    # axis
    axis = open3d.geometry.TriangleMesh.create_coordinate_frame(size=0.5 * scale)
    axis.transform(T)

    # points in pixel
    points_pixel = [
        [0, 0, 0],
        [0, 0, 1],
        [w, 0, 1],
        [0, h, 1],
        [w, h, 1],
    ]

    # pixel to camera coordinate system
    points = [Kinv @ p for p in points_pixel]

    # image plane
    width = abs(points[1][0]) + abs(points[3][0])
    height = abs(points[1][1]) + abs(points[3][1])
    plane = open3d.geometry.TriangleMesh.create_box(width, height, depth=1e-6)
    plane.paint_uniform_color(color)
    plane.translate([points[1][0], points[1][1], scale])
    plane.transform(T)

    # pyramid
    points_in_world = [(R @ p + t) for p in points]
    lines = [
        [0, 1],
        [0, 2],
        [0, 3],
        [0, 4],
    ]
    colors = [color for i in range(len(lines))]
    line_set = open3d.geometry.LineSet(
        points=open3d.utility.Vector3dVector(points_in_world),
        lines=open3d.utility.Vector2iVector(lines),
    )
    line_set.colors = open3d.utility.Vector3dVector(colors)

    # return as list in Open3D format
    return [axis, plane, line_set]
