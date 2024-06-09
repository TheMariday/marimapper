import colorsys

import cv2
import numpy as np
import open3d


def render_2d_model(led_map):
    display = np.ones((640, 640, 3)) * 0.2

    max_id = max(led_map.keys())

    for led_id in led_map:
        col = colorsys.hsv_to_rgb(led_id / max_id, 0.5, 1)
        image_point = (led_map[led_id]["pos"] * 640).astype(int)
        cv2.drawMarker(display, image_point, color=col)
        cv2.putText(
            display,
            str(led_id),
            image_point,
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            color=col,
        )

    cv2.imshow("MariMapper", display)
    cv2.waitKey(0)


def render_3d_model(led_map, cams=(), mesh=None, strips=None):
    if not led_map:
        return

    __vis = open3d.visualization.Visualizer()
    __vis.create_window(window_name="MariMapper", width=640, height=640)

    cam_geometry = []
    for K, R, t, width, height in cams:
        cam_geometry.extend(draw_camera(K, R, t, width, height))

    for c in cam_geometry:
        __vis.add_geometry(c)

    pcd = open3d.geometry.PointCloud()

    xyz = [led_map[led_id]["pos"] for led_id in led_map.keys()]
    normals = [led_map[led_id]["normal"] for led_id in led_map.keys()]

    pcd.points = open3d.utility.Vector3dVector(xyz)
    pcd.normals = open3d.utility.Vector3dVector(normals)

    if strips is not None:

        strip_points = []
        strip_connections = []
        colors = []

        for strip in strips:
            if not strip:
                continue
            strip_points.append(led_map[strip[0]]["pos"])
            for i in range(1, len(strip)):
                strip_points.append(led_map[strip[i]]["pos"])
                strip_connections.append([len(strip_points) - 2, len(strip_points) - 1])
                colors.append([1.0, 1.0, 1.0])

        line_set = open3d.geometry.LineSet(
            points=open3d.utility.Vector3dVector(strip_points),
            lines=open3d.utility.Vector2iVector(strip_connections),
        )
        line_set.colors = open3d.utility.Vector3dVector(colors)

        __vis.add_geometry(line_set)

    __vis.add_geometry(pcd)
    if mesh is not None:
        __vis.add_geometry(mesh)
    __vis.poll_events()
    __vis.update_renderer()

    view_ctl = __vis.get_view_control()
    view_ctl.set_up((0, 1, 0))
    view_ctl.set_lookat((0, 0, 0))
    view_ctl.set_zoom(0.3)

    render_options = __vis.get_render_option()
    render_options.point_show_normal = True
    render_options.point_color_option = (
        open3d.visualization.PointColorOption.YCoordinate
    )
    render_options.background_color = [0.2, 0.2, 0.2]

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

    # scale = 1
    color = [0.8, 0.8, 0.8]

    # intrinsics
    K = K.copy()
    Kinv = np.linalg.inv(K)

    # 4x4 transformation
    T = np.column_stack((R, t))
    T = np.vstack((T, (0, 0, 0, 1)))

    # axis
    # axis = open3d.geometry.TriangleMesh.create_coordinate_frame(size=0.5 * scale)
    # axis.transform(T)

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

    # pyramid
    points_in_world = [(R @ p + t) for p in points]
    lines = [
        [0, 1],
        [0, 2],
        [0, 3],
        [0, 4],
    ]
    colors = [color for _ in range(len(lines))]
    line_set = open3d.geometry.LineSet(
        points=open3d.utility.Vector3dVector(points_in_world),
        lines=open3d.utility.Vector2iVector(lines),
    )
    line_set.colors = open3d.utility.Vector3dVector(colors)

    # return as list in Open3D format
    return [line_set]
