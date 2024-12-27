from marimapper.led import LED2D, LED3D
from multiprocessing import Queue
from typing import Union, Any
from enum import Enum


class DetectionControlEnum(Enum):
    DETECT = 0
    SKIP = 1
    FAIL = 2
    DONE = 3
    DELETE = 4


class BaseQueue:

    def __init__(self):
        self._queue: Queue = Queue()
        self._queue.cancel_join_thread()

    def empty(self) -> bool:
        return self._queue.empty()


class RequestDetectionsQueue(BaseQueue):

    def request(self, led_id_from: int, led_id_to: int, view_id: int) -> None:
        self._queue.put((led_id_from, led_id_to, view_id))

    def get_id_from_id_to_view(self, timeout=None) -> tuple[int, int, int]:
        return self._queue.get(timeout=timeout)


class Queue2D(BaseQueue):

    def put(self, control: DetectionControlEnum, data: Union[LED2D, int, None]) -> None:
        self._queue.put((control, data))

    def get(self, timeout=None) -> tuple[DetectionControlEnum, Any]:
        return self._queue.get(timeout=timeout)


class Queue3D(BaseQueue):

    def put(self, leds: list[LED3D]) -> None:
        self._queue.put(leds)

    def get(self, timeout=None) -> list[LED3D]:
        return self._queue.get(timeout=timeout)

class Queue3DInfo(BaseQueue):

    def put(self, led_states: dict[int, int]) -> None:
        self._queue.put(led_states)

    def get(self, timeout=None) -> dict[int, int]:
        return self._queue.get(timeout=timeout)
