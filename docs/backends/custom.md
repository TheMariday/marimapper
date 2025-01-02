Open a new python file called `my_backend.py` and copy the below stub into it.

```python
class Backend:

    def __init__(self):
        # connect to some device here!

    def get_led_count(self) -> int:
        # return the number of leds your system can control here

    def set_led(self, led_index: int, on: bool) -> None:
        # Write your code for controlling your LEDs here
        # It should turn on or off the LED at the led_index depending on the "on" variable
        # For example:
        # if on:
        #     some_led_library.set_led(led_index, (255, 255, 255))
        # else:
        #     some_led_library.set_led(led_index, (0, 0, 0))
```

If your backend needs any external libraries for example, `requests`, add them to marimapper with `pipx inject marimapper requests` 

Fill out the blanks and check it by running `marimapper_check_backend --backend my_backend.py`
