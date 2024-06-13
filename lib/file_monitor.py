import os
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

    def exists(self):
        return os.path.isfile(self.filepath)


class DirectoryMonitor:

    def __init__(self, directory: Path):
        self.directory = directory
        self.current_files = self._get_filenames()

    def _get_filenames(self):
        return [
            self.directory / filename
            for filename in os.listdir(self.directory)
            if filename.startswith("led_map_2d")
        ]

    def has_changed(self):
        last_files = self.current_files
        self.current_files = self._get_filenames()
        return self.current_files != last_files
