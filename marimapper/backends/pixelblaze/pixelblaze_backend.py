from multiprocessing import get_logger
import time
import socket

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


def check_pixelblaze_reachable(ip, timeout=0.5):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, 81))
        sock.close()
        return result == 0
    except:
        return False


def discover_pixelblazes(timeout=3.0):
    logger.info(f"Listening for PixelBlaze beacon packets ({timeout}s)...")

    enumerator = pixelblaze.PixelblazeEnumerator()

    time.sleep(timeout)
    devices = enumerator.getPixelblazeList()
    enumerator.stop()

    logger.info(f"Found {len(devices)} PixelBlaze(s)")
    return devices


def pixelblaze_backend_factory(argparse_args: argparse.Namespace):
    return partial(Backend, argparse_args.server)


def pixelblaze_backend_set_args(parser):
    parser.add_argument(
        "--server",
        default="auto",
        help='IP address of PixelBlaze (default: "auto" - discovers first PixelBlaze on network)'
    )


class Backend:
    _pattern_cache = {}  # Class-level cache: source_code -> compiled bytecode
    _last_rendered_pattern = ""

    def __init__(self, pixelblaze_ip: str):
        self.pb = self.init_pixelblaze(pixelblaze_ip)
        self.switch_to_mapper_pattern()

    def init_pixelblaze(self, pixelblaze_ip: str):
        # Handle auto-discovery mode
        if pixelblaze_ip.lower() == "auto":
            logger.info("Auto-discovering PixelBlaze...")

            # First check Ad Hoc mode (fast)
            logger.info("Checking for Ad Hoc mode (192.168.4.1)...")
            if check_pixelblaze_reachable("192.168.4.1"):
                pixelblaze_ip = "192.168.4.1"
                logger.info("Found PixelBlaze in Ad Hoc mode at 192.168.4.1")
            else:
                # Try beacon scan on network
                devices = discover_pixelblazes(timeout=3.0)
                if devices:
                    first_device = devices[0]
                    pixelblaze_ip = first_device.get('address') if isinstance(first_device, dict) else str(first_device)
                    logger.info(f"Found PixelBlaze at {pixelblaze_ip}")
                else:
                    logger.error("No PixelBlazes found. Specify IP with --server")
                    raise RuntimeError("No PixelBlazes found on network")

        logger.info(f"PixelBlaze server: {pixelblaze_ip}")

        try:
            ip_address(pixelblaze_ip)
        except ValueError:
            raise RuntimeError(
                f"Pixelblaze backend failed to start due as {pixelblaze_ip} is not a valid IP address"
            )

        return pixelblaze.Pixelblaze(pixelblaze_ip)
    
    def switch_to_mapper_pattern(self):
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
        """Set arbitrary pixel colors. Buffer format: [[r, g, b], ...] where index is position in list"""

        # If setting all black or empty...
        if not buffer or all(rgb == [0, 0, 0] for rgb in buffer):
            self.switch_to_mapper_pattern()
            return

        try:
            self.render_pattern(RGB_PATTERN)

            # Scale 0-255 to 0-1 and flatten to [r,g,b,r,g,b,...] format
            colors = []
            for r, g, b in buffer:
                colors.extend([r / 255.0, g / 255.0, b / 255.0])

            # Send to pixelblaze
            self.pb.setActiveVariables({"colors": colors})
        except Exception as e:
            logger.error(f"Failed to set RGB pixels on PixelBlaze: {e}")

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
        if self._last_rendered_pattern == source_code:
            return

        """Sets current PixelBlaze renderer to this pattern source code, compiles and uses caching."""
        with open(Path(source_code), 'r', encoding='utf-8-sig') as f:
            source_code = f.read()

        # Check cache for compiled bytecode
        if source_code in self._pattern_cache:
            bytecode = self._pattern_cache[source_code]
        else:
            bytecode = self.pb.compilePattern(source_code)
            self._pattern_cache[source_code] = bytecode

        self._last_rendered_pattern = source_code
        self.pb.sendPatternToRenderer(bytecode)