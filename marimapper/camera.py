from argparse import ArgumentTypeError
from urllib.parse import urlsplit

import cv2
from multiprocessing import get_logger

logger = get_logger()

NETWORK_SCHEMES = ("http://", "https://", "rtsp://", "rtmp://")
NETWORK_TIMEOUT_MS = 5000


def is_network_stream(device_id) -> bool:
    return isinstance(device_id, str) and device_id.lower().startswith(NETWORK_SCHEMES)


def parse_device(text: str):
    """
    Turns the value of --device into something Camera can open.

    - "0", "1", ...              a camera index, returned as an int
    - "http://...", "rtsp://..." a network video stream, returned unchanged
    """
    text = text.strip()

    if text.isdigit():
        return int(text)

    if is_network_stream(text) and urlsplit(text).hostname:
        return text

    raise ArgumentTypeError(
        f"'{text}' is not a camera index or a stream URL like http://192.168.1.20:8080/video"
    )


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
            # without a timeout an unreachable address can block for half a minute
            params = [
                cv2.CAP_PROP_OPEN_TIMEOUT_MSEC,
                NETWORK_TIMEOUT_MS,
                cv2.CAP_PROP_READ_TIMEOUT_MSEC,
                NETWORK_TIMEOUT_MS,
            ]
        else:
            capture_methods = [cv2.CAP_DSHOW, cv2.CAP_V4L2, cv2.CAP_ANY]
            params = []

        for capture_method in capture_methods:
            self.device = cv2.VideoCapture(device_id, capture_method, params)
            if self.device.isOpened():
                logger.debug(
                    f"Connected to device {device_id} with capture method {capture_method}"
                )
                break

        if not self.device.isOpened():
            if network:
                raise RuntimeError(
                    f"Failed to connect to stream {device_id}. Check that the stream is running "
                    f"and that the URL opens in a web browser or a video player such as VLC"
                )
            raise RuntimeError(f"Failed to connect to camera {device_id}")

        if network:
            # a short buffer keeps the picture close to what the camera sees right now
            self.device.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            logger.info(
                "Network streams usually can't be controlled from here: if the image is too bright, "
                "lower the exposure on the camera or streaming software itself"
            )

        self.default_settings = CameraSettings(self)

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
