import cv2
import sys
sys.path.append('./')
from lib.color_print import cprint, Col


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
        cprint(f"Connecting to camera {device_id} ...")
        self.device_id = device_id
        self.device = cv2.VideoCapture(device_id)
        if self.device.isOpened():
            cprint(f"Connected to camera {device_id}")
        else:
            cprint(f"Failed to connect to camera {device_id}", format=Col.FAIL)
            quit()

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

        cprint(f"Setting camera resolution to {width} x {height} ...")

        self.device.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.device.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        new_width = self.get_width()
        new_height = self.get_height()

        if width != new_width or height != new_height:
            cprint(f"Failed to set camera {self.device_id} resolution to {width} x {height}", Col.WARNING)

        self.device.read()  # do not remove! do not ask why, just accept it

        cprint(f"Camera resolution set to {new_width} x {new_height}")

    def set_autofocus(self, mode, focus=0):

        cprint(f"Setting autofocus to mode {mode} with focus {focus}")

        if not self.device.set(cv2.CAP_PROP_AUTOFOCUS, mode):
            cprint(f"Failed to set autofocus to {mode}", Col.WARNING)

        if not self.device.set(cv2.CAP_PROP_FOCUS, focus):
            cprint(f"Failed to set focus to {focus}", Col.WARNING)

    def set_exposure_mode(self, mode):

        cprint(f"Setting exposure to mode {mode}")

        if not self.device.set(cv2.CAP_PROP_AUTO_EXPOSURE, mode):
            cprint(f"Failed to put camera into manual exposure mode {mode}", Col.FAIL)

    def set_gain(self, gain):

        cprint(f"Setting gain to {gain}")

        if not self.device.set(cv2.CAP_PROP_GAIN, gain):
            cprint(f"failed to set camera gain to {gain}", Col.WARNING)

    def set_exposure(self, exposure):

        cprint(f"Setting exposure to {exposure}")

        if not self.device.set(cv2.CAP_PROP_EXPOSURE, exposure):
            cprint(f"Failed to set exposure to {exposure}", Col.FAIL)

    def read(self):
        ret_val, image = self.device.read()
        if not ret_val:
            cprint("Failed to grab frame", Col.FAIL)
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def ditch_frames(self, count=20):
        for _ in range(count):
            self.read()
