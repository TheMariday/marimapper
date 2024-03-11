import argparse
import cv2
import numpy as np

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Visualises 2D and 3D maps")

    parser.add_argument(
        "filename",
        type=str,
        help="The file to visualise, currently only supports 2D mapping",
    )

    args = parser.parse_args()

    display = np.zeros((640, 640, 3))

    with open(args.filename, "r") as file:
        lines = file.readlines()
        file_points = []
        for line in lines:
            led_id, u, v = line.strip().split(",")
            file_points.append([led_id, float(u), float(v)])

        if len(file_points[0]) == 3:

            for point_id, point_u, point_v in file_points:
                image_point = (int(point_u * 640), int(point_v * 640))
                cv2.drawMarker(display, image_point, color=(0, 255, 0))
                cv2.putText(
                    display,
                    point_id,
                    image_point,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    color=(0, 0, 255),
                )

            cv2.imshow("Visualise", display)
            cv2.waitKey(0)

        if len(file_points[0]) == 4:
            raise NotImplementedError(
                "3D point cloud visualisation isn't implemented yet"
            )
