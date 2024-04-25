import time
import threading

from backends.fcmega.fcmega import FCMega


class Backend:

    def __init__(self, led_count: int):
        self.fc_mega = FCMega()
        self.leds = [(0, 0, 0) for _ in range(400)]
        self.running = True
        self.update_thread = threading.Thread(target=self._run)
        self.update_thread.start()

    def __del__(self):
        self.running = False

    def _run(self):
        while self.running:
            self.fc_mega.set_pixels(self.leds)
            self.fc_mega.update()
            time.sleep(0.02)

    def set_led(self, led_index: int, on: bool):

        self.leds[led_index] = (100, 100, 100) if on else (0, 0, 0)