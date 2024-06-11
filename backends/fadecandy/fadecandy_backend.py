from backends.fadecandy import opc


class Backend:

    def __init__(self, uri="localhost:7890"):
        self.client = opc.Client(uri)
        self.buffer = [(0, 0, 0) for _ in range(self.get_led_count())]
        self.client.put_pixels(self.buffer)

    def __del__(self):
        black = [(0, 0, 0) for _ in range(self.get_led_count())]
        self.client.put_pixels(black)
        self.client.put_pixels(black)

    def get_led_count(self):
        # return the number of LEDs in your system here
        return 64

    def set_led(self, led_index: int, on: bool):
        self.buffer[led_index] = (255, 255, 255) if on else (0, 0, 0)
        self.client.put_pixels(self.buffer)
        self.client.put_pixels(self.buffer)
