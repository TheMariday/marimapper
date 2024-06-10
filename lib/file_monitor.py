import os
import time
import hashlib
from pathlib import Path


class FileMonitor:

    def __init__(self, filepath: Path):
        self.filepath = filepath

        self.current_hash = self._get_hash()


    def _get_hash(self):
        if not os.path.isfile(self.filepath):
            return None
        with open(self.filepath, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    def file_changed(self):
        last_hash = self.current_hash
        self.current_hash = self._get_hash()
        return self.current_hash != last_hash

    def wait_for_change(self):
        while True:
            if self.file_changed():
                return

            time.sleep(1)


class DirectoryMonitor:

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.current_files = self._get_filenames()

    def _get_filenames(self):
        return [
            self.filepath / filename
            for filename in os.listdir(self.filepath)
            if filename.endswith(".csv")
        ]

    def has_changed(self):
        last_files = self.current_files
        self.current_files = self._get_filenames()
        return self.current_files != last_files

    def wait_for_change(self):
        while True:
            if self.has_changed():
                return

            time.sleep(1)
