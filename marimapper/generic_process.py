from multiprocessing import Process, Queue, Event


class GenericProcess(Process):

    def __init__(self):
        super().__init__()
        self._input_queue = Queue()
        self._output_queues: list[Queue] = []

        self._exit_event = Event()

    def get_input_queue(self) -> Queue:
        return self._input_queue

    def add_output_queue(self, queue: Queue):
        self._output_queues.append(queue)

    def running(self):
        return not self._exit_event.is_set()

    def stop(self):
        self._exit_event.set()
