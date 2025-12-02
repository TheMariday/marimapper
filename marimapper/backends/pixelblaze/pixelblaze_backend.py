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
from os import PathLike
import argparse

MARIMAPPER_PATTERN = Path(__file__).parent / "marimapper.js"
RGB_PATTERN = Path(__file__).parent / "rgb.js"

logger = get_logger()


def pixelblaze_backend_factory(argparse_args: argparse.Namespace):
    return partial(Backend, argparse_args.server)


def pixelblaze_backend_set_args(parser):
    parser.add_argument("--server", default="4.3.2.1")


class Backend:
    _pattern_cache = {}  # Class-level cache: source_code -> compiled bytecode

    def __init__(self, pixelblaze_ip: str):

        try:
            ip_address(pixelblaze_ip)
        except ValueError:
            raise RuntimeError(
                f"Pixelblaze backend failed to start due as {pixelblaze_ip} is not a valid IP address"
            )

        self.pb = pixelblaze.Pixelblaze(pixelblaze_ip)
        try:
            self.render_pattern(MARIMAPPER_PATTERN)
        except Exception as err:
            self.load_existing_pattern(MARIMAPPER_PATTERN.stem)

    def get_led_count(self):
        pixel_count = self.pb.getPixelCount()
        logger.info(f"Pixelblaze reports {pixel_count} pixels")
        return pixel_count

    def set_led(self, led_index: int, on: bool):
        self.pb.setActiveVariables({"pixel_to_light": led_index, "turn_on": on})
    
    def set_leds(self, buffer: list[list[int]]):
        """Set arbitrary pixel indices with RGB colors. Buffer format: [[index, r, g, b], ...]"""
        self.render_pattern(RGB_PATTERN)

        if not buffer:
            self.pb.setActiveVariables({"colors": []})
            return

        # Find the maximum index to size the array
        max_index = max(entry[0] for entry in buffer)
        colors = [None] * (max_index + 1)

        # Fill in the colors array, scaling 0-255 to 0-1
        for entry in buffer:
            index, r, g, b = entry[0], entry[1], entry[2], entry[3]
            colors[index] = [r / 255.0, g / 255.0, b / 255.0]

        # Send to pixelblaze
        self.pb.setActiveVariables({"colors": colors})

    def set_map_coordinates(self, pixelmap: list):
        result = self.pb.setMapCoordinates(pixelmap)
        if result is False:
            raise RuntimeError("Pixelblaze Backend failed to upload map coordinates.")
        self.pb.wsSendJson({"mapperFit": 0})

    def load_existing_pattern(self, pattern_name: str):
        try:
            self.pb.setActivePatternByName(
                pattern_name
            )  # Need to install marimapper.js to your pixelblaze
        except TypeError as e:
            if "'NoneType' has no len()" in str(e):
                raise RuntimeError(
                    f"Pixelblaze may have failed to find the effect '{pattern_name}'. "
                    f"Have you uploaded {pattern_name}.epe to your controller?"
                )
            else:
                raise e
    
    def render_pattern(self, source_code: PathLike | str):
        """Sets current PixelBlaze renderer to this pattern source code, compiles and uses caching."""
        with open(Path(source_code), 'r', encoding='utf-8-sig') as f:
            source_code = f.read()

        # Check cache for compiled bytecode
        if source_code in self._pattern_cache:
            bytecode = self._pattern_cache[source_code]
        else:
            bytecode = self.pb.compilePattern(source_code)
            self._pattern_cache[source_code] = bytecode

        self.pb.sendPatternToRenderer(bytecode)