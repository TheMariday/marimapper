# Custom Backend Instructions

Your backend isn't listed? You've your own LED driver? Well check you out clever-clogs!

Luckily, writing your own custom backend is super simple with a dash of Python!

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

Fill out the blanks and check it by running `marimapper_check_backend custom my_backend.py` in the same directory

Once you've checked it works, you can run marimapper in the same directory with `marimapper custom my_backend.py` and it will use your backend!

But my backend requires a library! Like `requests`! What do?

Pip: `pip install requests`
PipX:`pipx inject marimapper requests`
UV: `uv tool install marimapper --with requests`

If you think others would find your backend useful (behave), please drop me a Github Issue, 
find me on Telegram or open a pull request so we can add it into marimapper!