from marimapper.scanner import Scanner
from marimapper import multiprocessing_logging
import os
import signal
import argparse
from marimapper.utils import add_camera_args, add_backend_args

# PYCHARM DEVELOPER WARNING!
# You MUST enable "Emulate terminal in output console" in the run configuration or
# really weird  stuff happens with multiprocessing!


def main():
    multiprocessing_logging.info("Starting MariMapper")

    parser = argparse.ArgumentParser(description="Captures LED flashes to file")

    add_camera_args(parser)
    add_backend_args(parser)

    parser.add_argument(
        "--dir", type=str, help="The output folder for your capture", default="."
    )

    args = parser.parse_args()

    scanner = Scanner(cli_args=args)

    scanner.mainloop()
    scanner.close()

    # For some reason python refuses to actually exit here, so I'm brute forcing it
    os.kill(os.getpid(), signal.SIGINT)
    os.kill(os.getpid(), signal.CTRL_C_EVENT)


if __name__ == "__main__":
    main()
