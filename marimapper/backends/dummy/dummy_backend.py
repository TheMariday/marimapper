from functools import partial


def dummy_backend_factory():
    return partial(Backend)


def dummy_backend_set_args(parser):
    pass


class Backend:

    def __init__(self):
        pass

    def get_led_count(self):
        return 0

    def set_led(self, led_index: int, on: bool):
        pass
