from multiprocessing import get_logger

# see https://github.com/TheMariday/marimapper/issues/78
# why this is a UserWarning and not a DepreciationWarning is beyond me...
import warnings

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=UserWarning, module="py_mini_racer")
    import pixelblaze

from ipaddress import ip_address
from functools import partial
from pathlib import Path
import argparse

logger = get_logger()


def pixelblaze_backend_factory(argparse_args: argparse.Namespace):
    return partial(Backend, argparse_args.server)


def pixelblaze_backend_set_args(parser):
    parser.add_argument("--server", default="4.3.2.1")


class Backend:

    def __init__(self, pixelblaze_ip: str):

        try:
            ip_address(pixelblaze_ip)
        except ValueError:
            raise RuntimeError(
                f"Pixelblaze backend failed to start due as {pixelblaze_ip} is not a valid IP address"
            )

        self.pb = pixelblaze.Pixelblaze(pixelblaze_ip)
        with open(Path(__file__).parent / "marimapper.js", 'r', encoding='utf-8-sig') as f:
            source_code = f.read()
        bytecode = self.pb.compilePattern(source_code)
        self.pb.sendPatternToRenderer(bytecode)

    def get_led_count(self):
        pixel_count = self.pb.getPixelCount()
        logger.info(f"Pixelblaze reports {pixel_count} pixels")
        return pixel_count

    def set_led(self, led_index: int, on: bool):
        self.pb.setActiveVariables({"pixel_to_light": led_index, "turn_on": on})

    def set_map_coordinates(self, pixelmap: list):
        result = self.pb.setMapCoordinates(pixelmap)
        if result is False:
            raise RuntimeError("Pixelblaze Backend failed to upload map coordinates.")
        self.pb.wsSendJson({"mapperFit": 0})

    def set_current_map(self, pixelmap_name: str):
        self.pb.setActivePatternByName(pixelmap_name)
