# L3D LED Mapper

[![Supported Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue)]()
[![Windows](https://github.com/TheMariday/L3D/actions/workflows/test_windows.yml/badge.svg)](https://github.com/TheMariday/L3D/actions/workflows/test_windows.yml)
[![Ubuntu](https://github.com/TheMariday/L3D/actions/workflows/test_ubuntu.yml/badge.svg)](https://github.com/TheMariday/L3D/actions/workflows/test_ubuntu.yml)
[![MacOS](https://github.com/TheMariday/L3D/actions/workflows/test_mac.yml/badge.svg)](https://github.com/TheMariday/L3D/actions/workflows/test_mac.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

This is a selection of tools to map LEDs into 2D and 3D space using only your webcam!

This works best in a dim environment so please make sure your camera isn't pointing at any other light sources! (Test in
Step 1)

All scripts can be run with the `--help` argument to list optional parameters such as resolution, exposure and latency.

## Step 0: Install requirements

After downloading this repository and installing Python, run `pip install -r requirements.txt`

## Step 1: Run the camera checker (recommended)

This will check your camera is compatible with L3D.

Run `python scripts/check_camera.py`

Test LED identification by turning down the lights and holding a torch or led up to the camera
This should start with few warnings, no errors and produce a **very** dark image
with a single crosshair on centered on your LED:

![alt text](docs/images/camera_check.png "Camera Check window")

## Step 2: Write your LED interface

Your LEDs are as unique as you are,
so the fastest way to connect L3D to your system is to fill in the blanks
in [backends/custom/custom_backend.py](backends/custom/custom_backend.py):

```python
# import some_led_library

class Backend:

    def __init__(self, led_count: int):
        # Remove the following line after you have implemented the set_led function!
        raise NotImplementedError("Could not load backend as it has not been implemented, go implement it!")

    def set_led(self, led_index: int, on: bool):
        # Write your code for controlling your LEDs here
        # It should turn on or off the led at the led_index depending on the "on" variable
        # For example:
        # if on:
        #     some_led_library.set_led(led_index, (255, 255, 255))
        # else:
        #     some_led_library.set_led(led_index, (0, 0, 0))
        pass

```

You can test your backend with `python scripts/check_backend.py`

L3D also support the following pre-made backends. This can be selected in the following steps using the `--backend`
argument.

| Backend   | Supported |
|-----------|-----------|
| FadeCandy | yes       |
| WLED      | yes       |
| LCM       | todo      |

## Step 3: Run the LED latency checker (recommended)

After writing or choosing your backend, place one of your addressable LEDs in front of your camera

run `python scripts/check_latency.py --backend fadecandy`

Change `--backend` to whatever backend you're using.

Once complete, the recommended latency will be listed in the console in milliseconds.
This can be used in the following steps using the `--latency` argument to speed up scans

## Step 4: Capture a 2D map

Set up your LEDs in front of your camera and
run `python scripts/capture_sequence.py my_scan --led_count 64 --backend fadecandy`

Change `--led_count` to however many LEDs you want to scan and `--backend` to whatever backend you're using

This will produce a timestamped CSV file in the `my_scan` folder with led index, u and v values.

Run `python scripts/visualise.py <filename>` to visualise 2D or 3D map files.

## Step 5: Construct a 3D map

[It's time to thunderize!](https://cdn.jwplayer.com/previews/dtA2LXBr)

To create a 3D map, run `capture_sequence` multiple times from different views of your LEDs,
this can either be done by moving your webcam around your LEDs or rotating your LEDs.

You can move your webcam to wherever you like as long as your leds are mostly in view.

Try and get at least 3 views between 6° - 20° apart

Once you have a selection of 2D maps captured with the `capture_sequence` script,
run `python scripts/reconstruct.py my_scan`

This may take a while, however once complete will generate `reconstruction.csv` in the `my_scan` folder.

Here is an example reconstruction of Highbeam's body LEDs

![alt text](docs/images/reconstruct.png "Highbeam LED reconstruction")

## Step 5: Construct a mesh

If you have a high enough density 3d map, you can use the remesh tool to create a 3D mesh based on your leds!

Run `python scripts/remesh.py reconstruction.csv my_mesh.ply`

![alt text](docs/images/remesh.png "Highbeam LED mesh reconstruction")

# Feedback

I would really love to hear what you think and if you have any bugs or improvements, please raise them here or drop me a
line on [Telegram](https://t.me/themariday).

If you implement a backend that you think others might use, please raise a pull request or just drop me a message on
Telegram!

If you want a super speed PR, run flake8, flake8-bugbear and black before submitting changes!