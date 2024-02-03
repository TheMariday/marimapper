from backends.fadecandy import opc


class Backend:

    def __init__(self, led_count, uri="localhost:7890"):
        self.led_count = led_count
        self.client = opc.Client(uri)
        self.buffer = [(0, 0, 0) for _ in range(self.led_count)]

    def __del__(self):
        black = [(0, 0, 0) for _ in range(self.led_count)]
        self.client.put_pixels(black)
        self.client.put_pixels(black)

    def set_led(self, led_index: int, on: bool):

        self.buffer[led_index] = (255, 255, 255) if on else (0, 0, 0)
        self.client.put_pixels(self.buffer)
        self.client.put_pixels(self.buffer)
