import os
from pathlib import Path


def get_test_dir(path: str) -> Path:

    this_path = os.path.dirname(os.path.abspath(__file__))
    return Path(this_path) / path
