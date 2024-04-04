import argparse
import sys

sys.path.append("./")

from lib.remesher import remesh, save_mesh
from lib.map_read_write import read_3d_map
from lib.visualize_model import render_3d_model


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Convert 3D maps to meshes")

    parser.add_argument(
        "input_filename",
        type=str,
        help="the 3d map",
    )

    parser.add_argument(
        "output_filename", type=str, help="the 3d mesh", default="mesh.ply"
    )

    parser.add_argument("--detail", type=int, help="the detail of the mesh", default=12)

    args = parser.parse_args()

    led_map = read_3d_map(args.input_filename)
    mesh = remesh(led_map, args.detail)
    save_mesh(mesh, args.output_filename)

    render_3d_model(led_map, mesh=mesh)
