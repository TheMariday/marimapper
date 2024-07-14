![logo.png](docs%2Fimages%2Flogo.png)

[![Supported Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue)]()
[![Windows](https://github.com/TheMariday/MariMapper/actions/workflows/test_windows.yml/badge.svg)](https://github.com/TheMariday/MariMapper/actions/workflows/test_windows.yml)
[![Ubuntu](https://github.com/TheMariday/MariMapper/actions/workflows/test_ubuntu.yml/badge.svg)](https://github.com/TheMariday/MariMapper/actions/workflows/test_ubuntu.yml)
[![MacOS](https://github.com/TheMariday/MariMapper/actions/workflows/test_mac.yml/badge.svg)](https://github.com/TheMariday/MariMapper/actions/workflows/test_mac.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> [!CAUTION]
> [This tool does not currently support Python 3.12](https://github.com/TheMariday/marimapper/issues/27)

This is a tool to map addressable LEDs into 2D and 3D space using only your webcam!

The basic algorithms behind this is what I used to map [Highbeam](https://www.youtube.com/shorts/isdhMqDIR8k)
(Map pictured below)

![](docs/images/reconstruct_with_normals_and_strips.png)


## Step 0: Install

Marimapper supports the following pre-built backends:

- `fadecandy`
- [`wled`](https://kno.wled.ge/)
- [`fcmega`](https://github.com/TheMariday/FC-Mega)
- [`pixelblaze`](https://electromage.com/docs)

To install Marimapper with a 
`pixelblaze`
backend, download this repository and run 
`pip install .[pixelblaze]`

<details>
<summary>Using pixelblaze?</summary>
Using Pixelblaze as a backend requires you to upload the [`marimapper.epe`](marimapper/backends/pixelblaze/marimapper.epe) pattern to your pixelblaze before running Marimapper.
</details>

If you would like to write your own LED backend, just run `pip install .` 


## Step 1: Run the camera checker (recommended)


Run `marimapper_check_camera` to ensure your camera is compatible with MariMapper, or check the list below:

<details>

<summary>Working Cameras</summary>

- HP 4310 (settings may not revert)
- Logitech C920
- Dell Lattitude 5521 built-in
- HP Envy x360 built-in 
- If your camera works, please drop me a line so I can add it to the list!

</details>

> [IMPORTANT]
> Scripts on windows need to be appended with `.exe`


Test LED identification by turning down the lights and holding a torch or led up to the camera
This should start with few warnings, no errors and produce a **very** dark image
with a single crosshair on centered on your LED.

As long as your webcam has exposure control, this should even work in a relatively well lit room!

> [!TIP]
> You can append `--help` to any command to show you all argument options

![alt text](docs/images/camera_check.png "Camera Check window")


> [!TIP]
> If your camera doesn't support exposure adjustment, or the image is still too bright, try dimming the lights and playing around with the --exposure and --threshold arguments


## Step 2: Write your LED backend if needed

If your LED backend isn't supported, you need to write your own!
This is luckily very simple!

Open a new python file called `my_backend.py` and copy the below stub into it.

Fill out the blanks and check it by running `marimapper_check_backend --backend my_backend.py`

```python
class Backend:

    def __init__(self):
        # connect to some device here!

    def get_led_count(self) -> int:
        # return the number of leds your system can control here

    def set_led(self, led_index: int, on: bool) -> None:
        # Write your code for controlling your LEDs here
        # It should turn on or off the led at the led_index depending on the "on" variable
        # For example:
        # if on:
        #     some_led_library.set_led(led_index, (255, 255, 255))
        # else:
        #     some_led_library.set_led(led_index, (0, 0, 0))
```

## Step 3: [It's time to thunderize!](https://youtu.be/-5KJiHc3Nuc?t=121)

Run `marimapper my_scan --backend fadecandy` 

Change `fadecandy` to whatever backend you're using 
and `my_scan` to the directory you want to save your scan

Set up your LEDs so most of them are in view and when you're ready, type `y` when prompted with `Start scan? [y/n]`

This will turn each LED on and off in turn, do not move the camera or leds during capture!

If you just want a 2D map, this is where you can stop! 

Run `python scripts/view_2d_map.py my_scan/...` to visualise your map replacing `...` with the map name.

To capture a 3D map, rotate your leds or move your webcam to a new position

> [!TIP]
> As long as some of your leds are mostly in view, you can move your webcam to wherever you like!
> Try and get at least 3 views between 6° - 20° apart

Once you have at least 2 2d maps, a new window will appear showing the reconstructed 3D positions of your LEDs.

If it doesn't look quite right, add some more scans!

Here is an example reconstruction of a test tube of LEDs I have

![](docs/images/live_example.png)

<details>
<summary>How to move the model around</summary>

- Click and drag to rotate the model around. 
- Hold shift to roll the camera
- Use the scroll wheel to zoom in / out
- Use the `n` key to hide / show normals
- Use the `+` / `-` keys to increase / decrease point sizes
- Use `1`, `2` & `3` keys to change colour scheme
</details>

# Feedback

I would really love to hear what you think and if you have any bugs or improvements, please raise them here or drop me a
line on [Telegram](https://t.me/themariday).

You can also raise issues [on this repo's issues page](https://github.com/TheMariday/marimapper/issues)

If you implement a backend that you think others might use, 
please raise a [pull request](https://github.com/TheMariday/marimapper/pulls) 
or just drop me a message on [Telegram](https://t.me/themariday)!

# Licensing

The licensing on this is [GPLv3](LICENSE).

The TLDR is you can do anything you like with this as long as it's open source
