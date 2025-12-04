import os
import sys
import json
import re
from pathlib import Path


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


CONFIG_DIR = Path.home() / ".config" / "marimapper" / "windows"
_CACHE = {}


def position_window(name: str, x: int, y: int, w: int, h: int) -> list[int]:
    """
    Returns [x, y, width, height].
    Checks memory cache first.
    If not in cache, checks disk.
    If not on disk, returns defaults immediately.
    """
    if name in _CACHE:
        return _CACHE[name]

    clean_name = re.sub(r"[^\w\-_\. ]", "_", name)
    file_path = CONFIG_DIR / f"{clean_name}.json"

    defaults = {"x": x, "y": y, "width": w, "height": h}
    config = defaults.copy()

    if file_path.exists():
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                config.update(data)
        except Exception:
            pass

    # Return as list [x, y, w, h]
    result = [config["x"], config["y"], config["width"], config["height"]]
    _CACHE[name] = result
    return result
