class Backend:

    def __init__(self):
        raise NotImplementedError(
            "Could not load backend as it has not been implemented, go implement it!"
        )

    def get_led_count(self):
        # return the number of LEDs in your system here
        return 0

    def set_led(self, led_index: int, on: bool):
        pass
