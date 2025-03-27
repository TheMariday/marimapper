import argparse
from marimapper.backends.fadecandy import opc
from functools import partial


def fadecandy_backend_factory(argparse_args: argparse.Namespace):
    return partial(Backend, argparse_args.uri)


def fadecandy_backend_set_args(parser):
    parser.add_argument('--uri', default="localhost:7890")


class Backend:

    def __init__(self, uri: str):
        self.client = opc.Client(uri)
        self.buffer = [(0, 0, 0) for _ in range(self.get_led_count())]
        self.client.put_pixels(self.buffer)

    def get_led_count(self):
        return 64

    def set_led(self, led_index: int, on: bool):
        self.buffer[led_index] = (255, 255, 255) if on else (0, 0, 0)
        self.client.put_pixels(self.buffer)
        self.client.put_pixels(self.buffer)
