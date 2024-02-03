import logging
def AddCameraArgs(parser):
    parser.add_argument('--device', type=int, help='Camera device index', default=0)
    parser.add_argument('--width', type=int, help='Video width, uses camera default by default', default=-1)
    parser.add_argument('--height', type=int, help='Video height, uses camera default by default', default=-1)
    parser.add_argument('--exposure', type=int, help='Set exposure time, usually lower is shorter', default=-10)
    parser.add_argument('--threshold', type=int, help='Anything below this threshold will be disregarded', default=128)


def GetBackend(backend_name, led_count):
    logging.info(f"Initialising backend")

    if backend_name == "custom":
        from backends.custom import custom_backend
        return custom_backend.Backend(led_count)

    if backend_name == "fadecandy":
        from backends.fadecandy import fadecandy_backend
        return fadecandy_backend.Backend(led_count)

    if backend_name == "serial":
        from backends.serial import serial_backend
        return serial_backend.Backend(led_count)

    if backend_name == "wled":
        from backends.wled import wled_backend
        return wled_backend.Backend(led_count)

    if backend_name == "lcm":
        from backends.lcm import lcm_backend
        return lcm_backend.Backend(led_count)

    logging.critical("Invalid backend")

