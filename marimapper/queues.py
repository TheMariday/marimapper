from marimapper.led import LED2D, LED3D
from multiprocessing import Queue
from typing import Union, Any
from enum import Enum


class DetectionControlEnum(Enum):
    DETECT = 0
    FAIL = 1
    DONE = 2
    DELETE = 3


class BaseQueue:

    def __init__(self):
        self._queue: Queue = Queue()
        self._queue.cancel_join_thread()

    def queue(self):
        return self._queue

    def empty(self):
        return self._queue.empty()


class RequestDetectionsQueue(BaseQueue):

    def request(self, led_id_from: int, led_id_to: int, view_id: int) -> None:
        self._queue.put((led_id_from, led_id_to, view_id))

    def get_id_from_id_to_view(self) -> tuple[int, int, int]:
        return self._queue.get()


class Queue2D(BaseQueue):

    def put(self, control: DetectionControlEnum, data: Union[LED2D, int, None]) -> None:
        self._queue.put((control, data))

    def get(self) -> tuple[DetectionControlEnum, Any]:
        return self._queue.get()


class Queue3D(BaseQueue):

    def put(self, leds: list[LED3D]) -> None:
        self._queue.put(leds)

    def get(self) -> list[LED3D]:
        return self._queue.get()
