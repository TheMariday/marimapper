import cv2


class MockCamera:

    def __init__(self, device_id=0):
        self.current_frame = 0
        self.device_id = device_id

    def get_width(self):
        return 640

    def get_height(self):
        return 480

    def get_af_mode(self):
        return 0

    def get_focus(self):
        return 0

    def get_exposure_mode(self):
        return 0

    def get_exposure(self):
        return 0

    def get_gain(self):
        return 0

    def set_resolution(self, width, height):
        pass

    def set_autofocus(self, mode, focus=0):
        pass

    def set_exposure_mode(self, mode):
        pass

    def set_gain(self, gain):
        pass

    def set_exposure(self, exposure):
        pass

    def read(self):
        frame = self.read_frame(self.current_frame)
        self.current_frame += 1
        return frame

    def read_frame(self, frame_id):
        filename = f"test/MariMapper-Test-Data/9_point_box/cam_{self.device_id}/capture_{frame_id:04}.png"
        return cv2.cvtColor(cv2.imread(filename), cv2.COLOR_BGR2GRAY)

    def set_exposure_and_wait(
        self, exposure, max_frames_to_wait=20, min_brightness_change=2.0
    ):
        pass
