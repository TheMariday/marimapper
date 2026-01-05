import time
from enum import Enum
from threading import RLock, Thread
from camera import Camera
import logging

from marimapper.detector import find_led, find_led_in_image, draw_led_detections


class MMState(Enum):
    WAITING_FOR_BACKEND = 0
    TESTING = 1
    READY = 2
    SCANNING = 3
    STOPPING = 4


class Marimapper:

    def __init__(self, transition_callback=None, webcam_callback=None):
        self.state = MMState.WAITING_FOR_BACKEND
        self.state_lock = RLock()
        self.transition_callback = transition_callback
        self.webcam_callback = webcam_callback

        self.camera = Camera(0)

        self.running = True
        self.running_thread = Thread(target=lambda: self.run())
        self.running_thread.start()
        self.threshold = 128
        self.test_led = 0

        transition_callback(self.state)

    def backend_ready(self, ready):
        self._transition(MMState.READY if ready else MMState.WAITING_FOR_BACKEND)

    def __del__(self):
        self.stop()

    def stop(self):
        self.running = False
        if self.running_thread:
            self.running_thread.join()

    def _transition(self, state:MMState):
        with self.state_lock:
            if self._can_transition(state):
                self.state = state
                logging.info(f"Transitioning to {state}")
                if self.transition_callback is not None:
                    self.transition_callback(state)
                return True
            else:
                print(f"can't transition from {self.state} to {state}")
                return False

    def _can_transition(self, state):
        with self.state_lock:
            if state == self.state:
                return False

            if self.state == MMState.WAITING_FOR_BACKEND:
                return state == MMState.READY

            if self.state == MMState.TESTING:
                return state in [MMState.READY,MMState.WAITING_FOR_BACKEND]

            if self.state == MMState.READY:
                return state in [MMState.SCANNING, MMState.WAITING_FOR_BACKEND, MMState.TESTING]

            if self.state == MMState.SCANNING:
                return state in [MMState.STOPPING, MMState.READY, MMState.WAITING_FOR_BACKEND]

            if self.state == MMState.STOPPING:
                return state in [MMState.READY, MMState.WAITING_FOR_BACKEND]

            return False

    def do_scan(self, progress_callback, scan_range, backend):
        if not self._transition(MMState.SCANNING): return
        for i in scan_range:
            if self.state == MMState.STOPPING:
                break

            backend.set_led(i, True)
            time.sleep(0.2)
            backend.set_led(i, False)
            progress_callback(i, bool(i%3))

        self._transition(MMState.READY)
        return True

    def stop_scan(self):
        self._transition(MMState.STOPPING)

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

    def toggle_test(self):
        self._transition(MMState.TESTING if self.state == MMState.READY else MMState.READY)

    def update_test_led(self, led_id):
        self.test_led = led_id