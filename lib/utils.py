import sys
sys.path.append('./')
from lib.color_print import cprint, Col


def add_camera_args(parser):
    parser.add_argument('--device', type=int,
                        help='Camera device index, set to 1 if using a laptop with a USB webcam', default=0)
    parser.add_argument('--width', type=int,
                        help='Camera width, usually uses 640 by default', default=-1)
    parser.add_argument('--height', type=int,
                        help='Camera height, usually uses 480 by default', default=-1)
    parser.add_argument('--exposure', type=int,
                        help='Camera exposure, the lower the value, the darker the image', default=-10)
    parser.add_argument('--threshold', type=int,
                        help='LED detection threshold, reducing this number will reduce false positives', default=128)


def add_backend_args(parser):

    parser.add_argument("--backend", type=str, help="The backend used for led communication",
                        choices=["custom", "fadecandy", "wled", "lcm"], default="custom")

    parser.add_argument("--server", type=str, help="Some backends require a server")


def get_backend(backend_name, led_count, server=""):

    try:
        if backend_name == "custom":
            from backends.custom import custom_backend
            return custom_backend.Backend(led_count)

        if backend_name == "fadecandy":
            from backends.fadecandy import fadecandy_backend
            if server:
                return fadecandy_backend.Backend(led_count, server)
            else:
                return fadecandy_backend.Backend(led_count)

        if backend_name == "wled":
            from backends.wled import wled_backend
            if server:
                return wled_backend.Backend(server)
            else:
                return wled_backend.Backend()

        if backend_name == "lcm":
            from backends.lcm import lcm_backend
            return lcm_backend.Backend(led_count)

        raise RuntimeError("Invalid backend name")

    except NotImplementedError:
        cprint(f"Failed to initialise backend {backend_name}, you need to implement it or use the "
               f"--backend argument to select from the available backends", Col.FAIL)
        quit()
