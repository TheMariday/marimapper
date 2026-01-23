import time
from enum import Enum
from threading import RLock, Thread
from camera import Camera
import logging

from marimapper.detector import find_led_in_image, draw_led_detections



class Marimapper:

    def __init__(self, webcam_callback=None):
        self.webcam_callback = webcam_callback

        self.camera = Camera(0)

        self.running = True
        self.running_scan = True
        self.running_thread = Thread(target=lambda: self.run())
        self.running_thread.start()
        self.threshold = 128
        self.test_led = 0

    def __del__(self):
        self.stop()

    def stop(self):
        self.running = False
        if self.running_thread:
            self.running_thread.join()


    def do_scan(self, progress_callback, scan_range, backend):
        self.running_scan = True

        for i in scan_range:
            if not self.running_scan:
                break

            backend.set_led(i, True)
            time.sleep(0.2)
            backend.set_led(i, False)
            progress_callback(i, bool(i%3))

        return True

    def stop_scan(self):
        self.running_scan = False

    def set_camera_id(self, index):
        if self.camera.device_id == index: return True
        try:
            self.camera = Camera(index)
            return True
        except RuntimeError:
            return False

    def run(self):
        while self.running:
            image = self.camera.read()
            point2d = find_led_in_image(image, self.threshold)
            if point2d:
                draw_led_detections(image, point2d)
            self.webcam_callback(image)

    def set_camera_exposure(self, exposure):
        self.camera.set_exposure(exposure)

    def set_threshold(self, thresh):
        self.threshold = thresh

    def get_camera_exposure(self):
        return self.camera.get_exposure()

    def update_test_led(self, led_id):
        self.test_led = led_id