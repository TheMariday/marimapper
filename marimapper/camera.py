import re
from argparse import ArgumentTypeError

import cv2
from multiprocessing import get_logger

logger = get_logger()

# The port the Android DroidCam app serves its video on, and the path of its MJPEG stream
DROIDCAM_DEFAULT_PORT = 4747
DROIDCAM_VIDEO_PATH = "/video"

NETWORK_SCHEMES = ("http://", "https://", "rtsp://", "rtmp://")
NETWORK_TIMEOUT_MS = 5000

# host[:port][/path] where host is a name, an IPv4 address or a bracketed IPv6 address
_ADDRESS_PATTERN = re.compile(
    r"^(?P<host>\[[0-9A-Fa-f:.]+\]|[A-Za-z0-9._-]+)(?::(?P<port>\d+))?(?P<path>/\S*)?$"
)


def is_network_stream(device_id) -> bool:
    return isinstance(device_id, str) and device_id.lower().startswith(NETWORK_SCHEMES)


def parse_device(text: str):
    """
    Turns the value of --device into something Camera can open.

    - "0", "1", ...            a camera index, returned as an int
    - "192.168.1.20:4747"      an Android DroidCam phone, returned as http://192.168.1.20:4747/video
    - "192.168.1.20"           the same, using DroidCam's default port 4747
    - "192.168.1.20:4747/video/force/1280x720"  the same, with a path of your choice
    - "http://...", "rtsp://..." any other network camera, returned unchanged
    """
    text = text.strip()

    try:
        return int(text)
    except ValueError:
        pass

    if is_network_stream(text):
        return text

    match = _ADDRESS_PATTERN.match(text)
    if match is None:
        raise ArgumentTypeError(
            f"'{text}' is not a camera index or a network address like 192.168.1.20:4747"
        )

    port = int(match["port"]) if match["port"] else DROIDCAM_DEFAULT_PORT
    if not 1 <= port <= 65535:
        raise ArgumentTypeError(f"'{port}' is not a valid port number")

    path = match["path"] or DROIDCAM_VIDEO_PATH
    return f"http://{match['host']}:{port}{path}"


class CameraSettings:

    def __init__(self, camera):
        self.af_mode = camera.get_af_mode()
        self.focus = camera.get_focus()
        self.exposure_mode = camera.get_exposure_mode()
        self.exposure = camera.get_exposure()
        self.gain = camera.get_gain()

    def apply(self, camera):
        camera.set_autofocus(self.af_mode, self.focus)
        camera.set_exposure_mode(self.exposure_mode)
        camera.set_gain(self.gain)
        camera.set_exposure(self.exposure)


class Camera:

    def __init__(self, device_id):
        logger.info(f"Connecting to device {device_id} ...")
        self.device_id = device_id

        network = is_network_stream(device_id)

        if network:
            # a second backend wouldn't fix an unreachable address, it would just double the wait
            if cv2.videoio_registry.hasBackend(cv2.CAP_FFMPEG):
                capture_methods = [cv2.CAP_FFMPEG]
            else:
                capture_methods = [cv2.CAP_ANY]
        else:
            capture_methods = [cv2.CAP_DSHOW, cv2.CAP_V4L2, cv2.CAP_ANY]

        for capture_method in capture_methods:
            self.device = self._open(device_id, capture_method, network)
            if self.device.isOpened():
                logger.debug(
                    f"Connected to device {device_id} with capture method {capture_method}"
                )
                break

        if not self.device.isOpened():
            if network:
                raise RuntimeError(
                    f"Failed to connect to camera {device_id}. Check that the camera app is running, "
                    f"that this computer and the phone are on the same network, and that the address "
                    f"opens in a web browser"
                )
            raise RuntimeError(f"Failed to connect to camera {device_id}")

        if network:
            # a short buffer keeps the picture close to what the camera sees right now
            self.device.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            logger.info(
                "Network cameras usually can't be controlled from here: if the image is too bright, "
                "lower the exposure in the camera app"
            )

        self.default_settings = CameraSettings(self)

    @staticmethod
    def _open(device_id, capture_method, network):
        open_timeout = getattr(cv2, "CAP_PROP_OPEN_TIMEOUT_MSEC", None)
        read_timeout = getattr(cv2, "CAP_PROP_READ_TIMEOUT_MSEC", None)

        if network and open_timeout is not None and read_timeout is not None:
            # without this an unreachable address can block for half a minute
            params = [
                open_timeout,
                NETWORK_TIMEOUT_MS,
                read_timeout,
                NETWORK_TIMEOUT_MS,
            ]
            try:
                return cv2.VideoCapture(device_id, capture_method, params)
            except (TypeError, cv2.error):
                pass  # older OpenCV builds don't take open parameters

        return cv2.VideoCapture(device_id, capture_method)

    def reset(self):
        self.default_settings.apply(self)

    def get_af_mode(self):
        return int(self.device.get(cv2.CAP_PROP_AUTOFOCUS))

    def get_focus(self):
        return int(self.device.get(cv2.CAP_PROP_FOCUS))

    def get_exposure_mode(self):
        return int(self.device.get(cv2.CAP_PROP_AUTO_EXPOSURE))

    def get_exposure(self):
        return int(self.device.get(cv2.CAP_PROP_EXPOSURE))

    def get_gain(self):
        return int(self.device.get(cv2.CAP_PROP_GAIN))

    def set_autofocus(self, mode, focus=0):

        logger.debug(f"Setting autofocus to mode {mode} with focus {focus}")

        if not self.device.set(cv2.CAP_PROP_AUTOFOCUS, mode):
            logger.info(f"Failed to set autofocus to {mode}")

        if not self.device.set(cv2.CAP_PROP_FOCUS, focus):
            logger.info(f"Failed to set focus to {focus}")

    def set_exposure_mode(self, mode):

        logger.debug(f"Setting exposure to mode {mode}")

        if not self.device.set(cv2.CAP_PROP_AUTO_EXPOSURE, mode):
            logger.info(f"Failed to put camera into manual exposure mode {mode}")

    def set_gain(self, gain):

        logger.debug(f"Setting gain to {gain}")

        if not self.device.set(cv2.CAP_PROP_GAIN, gain):
            logger.info(f"failed to set camera gain to {gain}")

    def set_exposure(self, exposure: int) -> bool:

        logger.debug(f"Setting exposure to {exposure}")

        if not self.device.set(cv2.CAP_PROP_EXPOSURE, exposure):
            logger.info(f"Failed to set exposure to {exposure}")
            return False

        return True

    def eat(self, count=30):
        for _ in range(count):
            self.read()

    def read(self):
        ret_val, image = self.device.read()
        if not ret_val:
            raise Exception("Failed to read image")

        return image
