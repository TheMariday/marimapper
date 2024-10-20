from marimapper.scanner import Scanner
from multiprocessing import log_to_stderr
import os
import signal
import argparse
import logging
from marimapper.utils import add_camera_args, add_backend_args

# PYCHARM DEVELOPER WARNING!
# You MUST enable "Emulate terminal in output console" in the run configuration or
# really weird  stuff happens with multiprocessing!


logger = log_to_stderr()


def main():
    logger.info("Starting MariMapper")

    parser = argparse.ArgumentParser(description="Captures LED flashes to file")

    add_camera_args(parser)
    add_backend_args(parser)

    parser.add_argument("-v", "--verbose", action="store_true")

    parser.add_argument(
        "--dir", type=str, help="The output folder for your capture", default="."
    )

    args = parser.parse_args()

    if not os.path.isdir(args.dir):
        raise Exception(f"path {args.dir} does not exist")

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    scanner = Scanner(cli_args=args)

    scanner.mainloop()
    scanner.close()

    # For some reason python refuses to actually exit here when an error is thrown, so I'm brute forcing it
    os.kill(os.getpid(), signal.SIGINT)
    os.kill(os.getpid(), signal.CTRL_C_EVENT)


if __name__ == "__main__":
    main()
