from marimapper.led import LED2D, LED3D
from multiprocessing import Queue

class Queue2D:

    def __init__(self):
        self._queue = Queue()
        self._queue.cancel_join_thread()

    def __del__(self):
        pass # empty here!  

    def queue(self):
        return self._queue

    def put(self, control: int, led: LED2D):
        self._queue.put((control, led))

    def get(self) -> tuple[int, LED2D]:
        control, led = self._queue.get()
        return control, led


class Queue3D:

    def __init__(self):
        self._queue = Queue()
        self._queue.cancel_join_thread()

    def queue(self):
        return self._queue

    def put(self, leds: list[LED3D]):
        self._queue.put(leds)

    def get(self) -> list[LED3D]:
        return self._queue.get()