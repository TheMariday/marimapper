import cv2
from marimapper import logging


class CameraSettings:

    def __init__(self, camera):
        self.width = camera.get_width()
        self.height = camera.get_height()
        self.af_mode = camera.get_af_mode()
        self.focus = camera.get_focus()
        self.exposure_mode = camera.get_exposure_mode()
        self.exposure = camera.get_exposure()
        self.gain = camera.get_gain()

    def apply(self, camera):
        camera.set_resolution(self.width, self.height)
        camera.set_autofocus(self.af_mode, self.focus)
        camera.set_exposure_mode(self.exposure_mode)
        camera.set_gain(self.gain)
        camera.set_exposure(self.exposure)


class Camera:

    def __init__(self, device_id):
        logging.info(f"Connecting to camera {device_id} ...")
        self.device_id = device_id

        for capture_method in [cv2.CAP_DSHOW, cv2.CAP_V4L2, cv2.CAP_ANY]:
            self.device = cv2.VideoCapture(device_id, capture_method)
            if self.device.isOpened():
                logging.debug(
                    f"Connected to camera {device_id} with capture method {capture_method}"
                )
                break

        if not self.device.isOpened():
            logging.error(f"Failed to connect to camera {device_id}")

        self.set_resolution(self.get_width(), self.get_height())  # Don't ask

    def get_width(self):
        return int(self.device.get(cv2.CAP_PROP_FRAME_WIDTH))

    def get_height(self):
        return int(self.device.get(cv2.CAP_PROP_FRAME_HEIGHT))

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

    def set_resolution(self, width, height):

        logging.debug(f"Setting camera resolution to {width} x {height} ...")

        self.device.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.device.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        new_width = self.get_width()
        new_height = self.get_height()

        if width != new_width or height != new_height:
            logging.error(
                f"Failed to set camera {self.device_id} resolution to {width} x {height}",
            )

        logging.debug(f"Camera resolution set to {new_width} x {new_height}")

    def set_autofocus(self, mode, focus=0):

        logging.debug(f"Setting autofocus to mode {mode} with focus {focus}")

        if not self.device.set(cv2.CAP_PROP_AUTOFOCUS, mode):
            logging.error(f"Failed to set autofocus to {mode}")

        if not self.device.set(cv2.CAP_PROP_FOCUS, focus):
            logging.error(f"Failed to set focus to {focus}")

    def set_exposure_mode(self, mode):

        logging.debug(f"Setting exposure to mode {mode}")

        if not self.device.set(cv2.CAP_PROP_AUTO_EXPOSURE, mode):
            logging.error(f"Failed to put camera into manual exposure mode {mode}")

    def set_gain(self, gain):

        logging.debug(f"Setting gain to {gain}")

        if not self.device.set(cv2.CAP_PROP_GAIN, gain):
            logging.error(f"failed to set camera gain to {gain}")

    def set_exposure(self, exposure):

        logging.debug(f"Setting exposure to {exposure}")

        if not self.device.set(cv2.CAP_PROP_EXPOSURE, exposure):
            logging.error(f"Failed to set exposure to {exposure}")

    def set_exposure_and_wait(
        self, exposure, max_frames_to_wait=20, min_brightness_change=2.0
    ):

        initial_mean = cv2.mean(self.read())[0]

        self.set_exposure(exposure)

        for _ in range(max_frames_to_wait):
            mean = cv2.mean(self.read())[0]
            ratio = mean / initial_mean
            if ratio > min_brightness_change or 1 / ratio > min_brightness_change:
                return

    def read(self, color=False):
        ret_val, image = self.device.read()
        if not ret_val:
            logging.error("Failed to grab frame")

        if not color:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            return image
