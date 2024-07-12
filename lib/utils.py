import os
import sys
from lib import logging


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
        help="The backend used for led communication",
        choices=["custom", "fadecandy", "wled", "fcmega", "pixelblaze"],
        required=True,
    )

    parser.add_argument("--server", type=str, help="Some backends require a server")


def get_user_confirmation(prompt):

    try:
        uin = input(logging.colorise(prompt, logging.Col.BLUE))

        while uin.lower() not in ("y", "n"):
            uin = input()

    except KeyboardInterrupt:
        return False

    return uin == "y"


def get_backend(backend_name, server=""):
    try:
        if backend_name == "custom":
            from backends.custom import custom_backend

            return custom_backend.Backend()

        if backend_name == "fadecandy":
            from backends.fadecandy import fadecandy_backend

            if server:
                return fadecandy_backend.Backend(server)
            else:
                return fadecandy_backend.Backend()

        if backend_name == "wled":
            from backends.wled import wled_backend

            if server:
                return wled_backend.Backend(server)
            else:
                return wled_backend.Backend()

        if backend_name == "fcmega":
            from backends.fcmega import fcmega_backend

            return fcmega_backend.Backend()
       
        if backend_name == "pixelblaze":
            from backends.pixelblaze import pixelblaze_backend

            return pixelblaze_backend.Backend(server)

        raise RuntimeError("Invalid backend name")

    except NotImplementedError:
        logging.error(
            f"Failed to initialise backend {backend_name}, you need to implement it or use the "
            f"--backend argument to select from the available backends"
        )
        quit()


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
