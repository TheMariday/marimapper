from marimapper import custom_ui_elements as viser_custom


from marimapper.backends.fcmega.fcmega import FCMega
from marimapper.custom_ui_elements import notify


class FCMegaBackend:

    def __init__(self):
        self.fc_mega = FCMega()
        self.leds = [(0, 0, 0) for _ in range(self.get_led_count())]


    def get_led_count(self):
        return 24 * 400

    def set_led(self, led_index: int, on: bool):

        self.leds[led_index] = (100, 100, 100) if on else (0, 0, 0)

        self.fc_mega.set_pixels(self.leds)
        self.fc_mega.update()


class BackendUI:
    name = "FCMega"
    def __init__(self, gui, on_ready):
        self.backend = None
        self.button = gui.add_button("Connect")
        self.button.on_click(self.connect_disconnect)
        self.on_ready = on_ready

    def connect_disconnect(self, event):
        try:
            with viser_custom.ProgressWrapper(self.button):
                if self.backend is None:
                    self.backend = FCMegaBackend()
                    self.button.label = "Disconnect"
                    self.on_ready(True)
                    notify(event.client, f"Connected to FCMega")
                else:
                    self.on_ready(False)
                    self.backend = None
                    self.button.label = "Connect"
                    notify(event.client, f"Disconnected from FCMega")

        except RuntimeError as e:
            notify(event.client, f"Failed to {self.button.label} from fc mega due to: {e.__str__()}")

    def disconnect(self):
        self.backend = None
        self.on_ready(False)

    def remove(self):
        self.button.remove()

    def enable(self):
        self.button.disable = False

    def disable(self):
        self.button.disable = True

    def get_backend(self):
        return self.backend