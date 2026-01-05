import time

from marimapper import custom_ui_elements as viser_custom

class Backend:
    def __init__(self):
        pass

    def connected(self):
        return True

    def state(self):
        return "I'm ready!"

class BackendUI:
    name = "PixelBlaze"
    def __init__(self, gui, on_ready):
        self.ip_address_text = gui.add_text("Server: ","4.3.2.1")
        self.button = gui.add_button("Connect")
        self.button.on_click(self.on_connect)
        self.backend = Backend()
        self.on_ready = on_ready

    def remove(self):
        self.button.remove()
        self.ip_address_text.remove()

    def enable(self):
        self.button.disabled = False

    def disable(self):
        self.button.disabled = True

    def on_connect(self,event):
        if not event.client: return

        with viser_custom.ProgressWrapper(self.button):
            self.ip_address_text.disabled = True

            if self.button.label == "Connect":
                viser_custom.notify(event.client, f"connecting to {self.ip_address_text.value}")
                time.sleep(1)
                viser_custom.notify(event.client, f"connected to {self.ip_address_text.value}")
                self.button.label = "Disconnect"
                self.on_ready(True)

            else:
                viser_custom.notify(event.client, f"Disconnected from {self.ip_address_text.value}")
                self.button.label = "Connect"
                self.ip_address_text.disabled = False
                self.on_ready(False)

    def get_backend(self):
        return self.backend