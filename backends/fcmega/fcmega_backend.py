import time
import threading

from backends.fcmega.fcmega import FCMega


class Backend:

    def __init__(self):
        self.fc_mega = FCMega()
        self.leds = [(0, 0, 0) for _ in range(self.get_led_count())]
        self.running = True
        self.update_thread = threading.Thread(target=self._run)
        self.update_thread.start()

    def __del__(self):
        self.running = False

    def get_led_count(self):
        return 24*400

    def _run(self):
        while self.running:
            self.fc_mega.set_pixels(self.leds)
            self.fc_mega.update()
            time.sleep(0.02)

    def set_led(self, led_index: int, on: bool):

        self.leds[led_index] = (100, 100, 100) if on else (0, 0, 0)
