import cv2
import numpy as np

from multiprocessing import get_logger

logging = get_logger()


class MockCamera:

    def __init__(self, device_id):

        self.frame_id = 0

        logging.info(f"Connecting to camera {device_id} ...")
        self.device_id = device_id
        self.device = cv2.VideoCapture(device_id)
        real_frames = []
        while True:
            ret_val, image = self.device.read()
            if not ret_val:
                break
            real_frames.append(image)

        self.frames = []
        black = np.zeros(real_frames[0].shape)
        for frame in real_frames:
            self.frames.append(black)
            self.frames.append(frame)
            self.frames.append(black)

    def reset(self):
        pass

    def get_af_mode(self):
        return 1

    def get_focus(self):
        return 1

    def get_exposure_mode(self):
        return 1

    def get_exposure(self):
        return 1

    def get_gain(self):
        return 1

    def set_autofocus(self, mode, focus=0):
        pass

    def set_exposure_mode(self, mode):
        pass

    def set_gain(self, gain):
        pass

    def set_exposure(self, exposure):
        pass

    def eat(self, count=30):
        pass

    def read(self, color=False):

        frame = self.frames[self.frame_id]
        self.frame_id += 1

        return frame
