import os
import sys

import importlib.util
import importlib.metadata
import logging

logger = logging.getLogger()


def get_user_confirmation(prompt):  # pragma: no coverage

    try:
        uin = input(prompt)

        while uin.lower() not in ("y", "n"):
            uin = input(prompt)

    except KeyboardInterrupt:
        return False

    return uin == "y"


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


def backend_black(backend):
    buffer = [[0, 0, 0] for _ in range(backend.get_led_count())]
    try:
        backend.set_leds(buffer)
        return True
    except AttributeError:
        return False


def get_marimapper_version() -> str:  # pragma: no cover

    return importlib.metadata.version("marimapper")  # pragma: no cover
