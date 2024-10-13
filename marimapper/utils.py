import os
import sys

import importlib.util
from inspect import signature

from marimapper import logging


def add_camera_args(parser):
    parser.add_argument(
        "--device",
        type=int,
        help="Camera device index, set to 1 if using a laptop with a USB webcam",
        default=0,
    )
    parser.add_argument(
        "--width",
        type=int,
        help="Camera width, usually uses 640 by default",
        default=-1,
    )
    parser.add_argument(
        "--height",
        type=int,
        help="Camera height, usually uses 480 by default",
        default=-1,
    )
    parser.add_argument(
        "--exposure",
        type=int,
        help="Camera exposure, the lower the value, the darker the image",
        default=-10,
    )
    parser.add_argument(
        "--threshold",
        type=int,
        help="LED detection threshold, reducing this number will reduce false positives",
        default=128,
    )


def add_backend_args(parser):
    parser.add_argument(
        "--backend",
        type=str,
        help="The backend used for led communication, i.e. fadecandy, wled or my_backend.py",
        default="None",
    )

    parser.add_argument(
        "--start", type=int, help="Index of the first led you want to scan", default=0
    )
    parser.add_argument(
        "--end",
        type=int,
        help="Index of the last led you want to scan up to the backends limit",
        default=10000,
    )

    parser.add_argument("--server", type=str, help="Some backends require a server")


def get_user_confirmation(prompt):  # pragma: no coverage

    try:
        uin = input(logging.colorise(prompt, logging.Col.BLUE))

        while uin.lower() not in ("y", "n"):
            uin = input()

    except KeyboardInterrupt:
        return False

    return uin == "y"


def load_custom_backend(backend_file, server=None):

    custom_backend_specs = importlib.util.spec_from_file_location(
        "custom_backend", backend_file
    )
    custom_backend = importlib.util.module_from_spec(custom_backend_specs)

    custom_backend_specs.loader.exec_module(custom_backend)

    backend = custom_backend.Backend(server) if server else custom_backend.Backend()

    check_backend(backend)

    return backend


def check_backend(backend):

    missing_funcs = {"get_led_count", "set_led"}.difference(set(dir(backend)))

    if missing_funcs:
        raise RuntimeError(
            f"Your backend does not have the following functions: {missing_funcs}"
        )

    if len(signature(backend.get_led_count).parameters) != 0:  # pragma: no coverage
        raise RuntimeError(
            "Your backend get_led_count function should not take any arguments"
        )

    if len(signature(backend.set_led).parameters) != 2:
        raise RuntimeError(
            "Your backend set_led function should only take two arguments"
        )


def get_backend(backend_name, server=""):
    if backend_name == "fadecandy":
        from marimapper.backends.fadecandy import fadecandy_backend

        if server:
            return fadecandy_backend.Backend(server)
        else:
            return fadecandy_backend.Backend()

    if backend_name == "wled":
        from marimapper.backends.wled import wled_backend

        if server:
            return wled_backend.Backend(server)
        else:
            return wled_backend.Backend()

    if backend_name == "fcmega":
        from marimapper.backends.fcmega import fcmega_backend

        return fcmega_backend.Backend()

    if backend_name == "pixelblaze":
        from marimapper.backends.pixelblaze import pixelblaze_backend

        return pixelblaze_backend.Backend(server)

    if os.path.isfile(backend_name) and backend_name.endswith(".py"):
        return load_custom_backend(backend_name, server)

    if backend_name == "None":
        return None

    raise RuntimeError("Invalid backend name")


class SupressLogging(object):
    def __enter__(self):
        self.outnull_file = open(os.devnull, "w")
        self.errnull_file = open(os.devnull, "w")

        self.old_stdout_fileno_undup = sys.stdout.fileno()
        self.old_stderr_fileno_undup = sys.stderr.fileno()

        self.old_stdout_fileno = os.dup(sys.stdout.fileno())
        self.old_stderr_fileno = os.dup(sys.stderr.fileno())

        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr

        os.dup2(self.outnull_file.fileno(), self.old_stdout_fileno_undup)
        os.dup2(self.errnull_file.fileno(), self.old_stderr_fileno_undup)

        sys.stdout = self.outnull_file
        sys.stderr = self.errnull_file
        return self

    def __exit__(self, *_):
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr

        os.dup2(self.old_stdout_fileno, self.old_stdout_fileno_undup)
        os.dup2(self.old_stderr_fileno, self.old_stderr_fileno_undup)

        os.close(self.old_stdout_fileno)
        os.close(self.old_stderr_fileno)

        self.outnull_file.close()
        self.errnull_file.close()
