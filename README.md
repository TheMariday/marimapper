# MariMapper

[![Supported Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue)]()
[![Windows](https://github.com/TheMariday/MariMapper/actions/workflows/test_windows.yml/badge.svg)](https://github.com/TheMariday/MariMapper/actions/workflows/test_windows.yml)
[![Ubuntu](https://github.com/TheMariday/MariMapper/actions/workflows/test_ubuntu.yml/badge.svg)](https://github.com/TheMariday/MariMapper/actions/workflows/test_ubuntu.yml)
[![MacOS](https://github.com/TheMariday/MariMapper/actions/workflows/test_mac.yml/badge.svg)](https://github.com/TheMariday/MariMapper/actions/workflows/test_mac.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

![logo.png](docs%2Fimages%2Flogo.png)

This is a selection of tools to map LEDs into 2D and 3D space using only your webcam!

> [!TIP]
> All scripts can be run with the `--help` argument to list optional parameters such as resolution and exposure.

## Step 0: Install requirements

After downloading this repository and installing Python, run `pip install -r requirements.txt`

## Step 1: Run the camera checker (recommended)

Run `python scripts/check_camera.py` to ensure your camera is compatible with MariMapper, or check the list below:

<details>

<summary>Working Cameras</summary>

- HP 4310 (settings may not revert)
- Logitech C920
- Dell Lattitude 5521 built-in
- HP Envy x360 built-in 

</details>

Test LED identification by turning down the lights and holding a torch or led up to the camera
This should start with few warnings, no errors and produce a **very** dark image
with a single crosshair on centered on your LED:

> [!IMPORTANT]
> This works best in a dim environment so please make sure your camera isn't pointing at any other light sources!

![alt text](docs/images/camera_check.png "Camera Check window")

## Step 2: Write your LED interface

Your LEDs are as unique as you are,
so the fastest way to connect MariMapper to your system is to fill in the blanks
in [backends/custom/custom_backend.py](backends/custom/custom_backend.py):

```python
# import some_led_library

class Backend:

    def __init__(self):
        # Remove the following line after you have implemented the set_led function!
        raise NotImplementedError("Could not load backend as it has not been implemented, go implement it!")

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

```

You can test your backend with `python scripts/check_backend.py`

MariMapper also support the following pre-made backends. This can be selected in the following steps using the `--backend`
argument.

- [x] Fadecandy / OPC
- [x] [WLED](https://kno.wled.ge/)
- [x] [FC Mega](https://github.com/TheMariday/FC-Mega)
- [ ] [LCM](https://lcm-proj.github.io/lcm/)


## Step 3: Capture a 2D map

Set up your LEDs in front of your camera and
run `python scripts/capture_sequence.py my_scan --backend fadecandy`

Change `--backend` to whatever backend you're using

This will produce a timestamped CSV file in the `my_scan` folder with led index, u and v values.

Run `python scripts/visualise.py <filename>` to visualise 2D or 3D map files.

## Step 4: Construct a 3D map

[It's time to thunderize!](https://youtu.be/-5KJiHc3Nuc?t=121)

To create a 3D map, run `capture_sequence` multiple times from different views of your LEDs,
this can either be done by moving your webcam around your LEDs or rotating your LEDs.

> [!TIP]
> You can move your webcam to wherever you like as long as some of your leds are mostly in view
> Try and get at least 3 views between 6° - 20° apart

Once you have a selection of 2D maps captured with the `capture_sequence.py` script,
run `python scripts/reconstruct.py my_scan`

This may take a while, however once complete will generate `reconstruction.csv` in the `my_scan` folder.

Here is an example reconstruction of Highbeam's body LEDs

![alt text](docs/images/reconstruct_with_normals_and_strips.png "Highbeam LED reconstruction")

<details>
<summary>How to move the model around</summary>

- Click and drag to rotate the model around. 
- Hold shift to roll the camera
- Use the scroll wheel to zoom in / out
- Use the `n` key to hide / show normals
- Use the `+` / `-` keys to increase / decrease point sizes
- Use `1`, `2` & `3` keys to change colour scheme
</details>


## Step 5: Construct a mesh (optional)

If you have a high enough density 3d map, you can use the remesh tool to create a 3D mesh based on your leds!

Run `python scripts/remesh.py reconstruction.csv my_mesh.ply`

This will generate a ply file which you can open and look at with your eyes

![alt text](docs/images/remesh_with_normals.png "Highbeam LED mesh reconstruction")

# Feedback

I would really love to hear what you think and if you have any bugs or improvements, please raise them here or drop me a
line on [Telegram](https://t.me/themariday).

If you implement a backend that you think others might use, please raise a pull request or just drop me a message on
Telegram!

If you want a super speed PR, run flake8, flake8-bugbear and black before submitting changes!
