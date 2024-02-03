import cv2
import logging


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
        self.device = cv2.VideoCapture(device_id)
        if self.device.isOpened():
            logging.info(f"Connected to camera {device_id}")
        else:
            logging.critical(f"Failed to connect to camera {device_id}")

        self.set_resolution(self.get_width(), self.get_height())  # Don't ask

    def __repr__(self):
        return f"""Resolution: {self.get_width()} x {self.get_height()}
Autofocus mode: {self.get_af_mode()}
Focus: {self.get_focus()}
Exposure mode: {self.get_exposure_mode()}
Exposure: {self.get_exposure()}
Gain: {self.get_gain()}"""


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

        logging.info(f"Setting camera resolution to {width} x {height} ...")

        self.device.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.device.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        new_width = self.get_width()
        new_height = self.get_height()

        if width != new_width or height != new_height:
            logging.error(f"Failed to set camera {self.device_id} resolution to {width} x {height}")

        self.device.read()  # do not remove! do not ask why, just accept it

        logging.info(f"Camera resolution set to {new_width} x {new_height}")


    def set_autofocus(self, mode, focus=0):

        logging.info(f"Setting autofocus to mode {mode} with focus {focus}")

        if not self.device.set(cv2.CAP_PROP_AUTOFOCUS, mode):
            logging.warning(f"Failed to set autofocus to {mode}")

        if not self.device.set(cv2.CAP_PROP_FOCUS, focus):
            logging.warning(f"Failed to set focus to {focus}")

    def set_exposure_mode(self, mode):

        logging.info(f"Setting exposure to mode {mode}")

        if not self.device.set(cv2.CAP_PROP_AUTO_EXPOSURE, mode):
            logging.error(f"Failed to put camera into manual exposure mode {mode}")

    def set_gain(self, gain):

        logging.info(f"Setting gain to {gain}")

        if not self.device.set(cv2.CAP_PROP_GAIN, gain):
            logging.warning(f"failed to set camera gain to {gain}")

    def set_exposure(self, exposure):

        logging.info(f"Setting exposure to {exposure}")

        if not self.device.set(cv2.CAP_PROP_EXPOSURE, exposure):
            logging.warning(f"Failed to set exposure to {exposure}")

    def read(self):
        ret_val, image = self.device.read()
        if not ret_val:
            logging.warning("Failed to grab frame")
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

