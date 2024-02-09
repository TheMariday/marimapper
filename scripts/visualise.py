import argparse
import cv2
import numpy as np

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Visualises 2D and 3D maps')

    parser.add_argument("filename", type=str, help="The file to visualise, currently only supports 2D mapping")

    args = parser.parse_args()

    file_resolution = [int(r) for r in args.filename.replace(".csv", "").split("_")[-2:]]

    display = np.zeros((file_resolution[1], file_resolution[0], 3))

    with open(args.filename, "r") as file:
        lines = file.readlines()
        file_points = [[int(v) for v in line.strip().split(",")] for line in lines]

        if len(file_points[0]) == 3:

            for point_id, point_u, point_v in file_points:
                image_point = (int(point_u), int(point_v))
                cv2.drawMarker(display, image_point, color=(0, 255, 0))
                cv2.putText(display, f"{point_id}", image_point, cv2.FONT_HERSHEY_SIMPLEX, 1, color=(0, 0, 255))

            cv2.imshow("Visualise", display)
            cv2.waitKey(0)

        if len(file_points[0]) == 4:
            raise NotImplementedError("3D point cloud visualisation isn't implemented yet")
