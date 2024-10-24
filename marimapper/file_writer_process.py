from multiprocessing import Process, Queue, Event
import time
from marimapper.file_tools import write_3d_leds_to_file, write_2d_leds_to_file
from pathlib import Path
import os

from marimapper.led import LED2D


class FileWriterProcess(Process):

    def __init__(self, base_path: Path):
        super().__init__()
        self._input_queue_2d = Queue()
        self._input_queue_2d.cancel_join_thread()
        self._input_queue_3d = Queue()
        self._input_queue_3d.cancel_join_thread()
        self._exit_event = Event()
        self._base_path = base_path
        os.makedirs(self._base_path, exist_ok=True)

    def stop(self):
        self._exit_event.set()

    def get_2d_input_queue(self):
        return self._input_queue_2d

    def get_3d_input_queue(self):
        return self._input_queue_3d

    def get_new_filename(self) -> Path:
        string_time = time.strftime("%Y%m%d-%H%M%S")
        return self._base_path / f"led_map_2d_{string_time}.csv"

    # This function is a bit gross and needs cleaning up
    def run(self):
        views = {}
        view_id_to_filename = {}

        requires_update = set()

        while not self._exit_event.is_set():
            if not self._input_queue_3d.empty():
                leds = self._input_queue_3d.get()
                write_3d_leds_to_file(leds, self._base_path / "led_map_3d.csv")

            if not self._input_queue_2d.empty():
                led: LED2D = self._input_queue_2d.get()
                if led.point is not None:
                    if led.view_id not in view_id_to_filename:
                        view_id_to_filename[led.view_id] = self.get_new_filename()
                        views[led.view_id] = []

                    views[led.view_id].append(led)
                    requires_update.add(led.view_id)

            else:
                for view_id in requires_update:
                    write_2d_leds_to_file(views[view_id], view_id_to_filename[view_id])
                requires_update = set()
                time.sleep(1)

        # clear the queues, don't ask why.
        while not self._input_queue_2d.empty():
            self._input_queue_2d.get()
        while not self._input_queue_3d.empty():
            self._input_queue_3d.get()
