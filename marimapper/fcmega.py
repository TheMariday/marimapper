from marimapper.backends.fcmega.fcmega import FCMega


class FCMegaBackend:
    def __init__(self, gui):
        self.something = gui.add_text("something","")

        self.fc_mega = None
        self.leds = [(0, 0, 0) for _ in range(24 * 400)]

    def connect(self):
        self.fc_mega = FCMega()
        return True

    def disconnect(self):
        self.fc_mega = None

    def remove(self):
        self.something.remove()

    def set_led(self, led_index: int, on: bool):

        if self.fc_mega:

            self.leds[led_index] = (100, 100, 100) if on else (0, 0, 0)
            self.fc_mega.set_pixels(self.leds)
            self.fc_mega.update()

    def disabled(self, disabled):
        self.something.disabled = disabled

    def to_json(self):
        return {"something": self.something.value}

    def from_json(self, json_data):
        self.something.value = json_data["something"]
