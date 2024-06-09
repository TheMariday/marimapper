# import some_led_library


class Backend:

    def __init__(self):
        # Remove the following line after you have implemented the set_led function!
        raise NotImplementedError(
            "Could not load backend as it has not been implemented, go implement it!"
        )

    def get_led_count(self):
        # return the number of LEDs in your system here
        return 0

    def set_led(self, led_index: int, on: bool):
        # Write your code for controlling your LEDs here
        # It should turn on or off the led at the led_index depending on the "on" variable
        # For example:
        # if on:
        #     some_led_library.set_led(led_index, (255, 255, 255))
        # else:
        #     some_led_library.set_led(led_index, (0, 0, 0))
        pass
