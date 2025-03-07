from multiprocessing import Process, Event
from marimapper.queues import Queue2D, Queue3D, DetectionControlEnum
from marimapper.led import LED2D
import time
from marimapper.file_tools import write_3d_leds_to_file, write_2d_leds_to_file
from pathlib import Path
import os


class FileWriterProcess(Process):

    def __init__(self, base_path: Path):
        super().__init__()
        self._input_queue_2d = Queue2D()
        self._input_queue_3d = Queue3D()
        self._exit_event = Event()
        self._base_path = base_path
        os.makedirs(self._base_path, exist_ok=True)
        self.daemon = True

    def stop(self):
        self._exit_event.set()

    def get_2d_input_queue(self):
        return self._input_queue_2d

    def get_3d_input_queue(self):
        return self._input_queue_3d

    def get_new_filename(self) -> Path:
        string_time = time.strftime("%Y%m%d-%H%M%S")
        return self._base_path / f"led_map_2d_{string_time}.csv"

    def run(self):
        views: dict[int, list[LED2D]] = {}
        view_id_to_filename: dict[int, Path] = {}

        while not self._exit_event.is_set():

            if not self._input_queue_3d.empty():
                leds = self._input_queue_3d.get()
                write_3d_leds_to_file(leds, self._base_path / "led_map_3d.csv")

            if not self._input_queue_2d.empty():
                control, data = self._input_queue_2d.get()

                if control == DetectionControlEnum.DONE:
                    view_id = data
                    write_2d_leds_to_file(views[view_id], view_id_to_filename[view_id])

                if control == DetectionControlEnum.DETECT:
                    led = data

                    if led.view_id not in view_id_to_filename:
                        view_id_to_filename[led.view_id] = self.get_new_filename()
                        views[led.view_id] = []

                    views[led.view_id].append(led)

                if control == DetectionControlEnum.DELETE:
                    view_id = data
                    del views[view_id]
                    del view_id_to_filename[view_id]
