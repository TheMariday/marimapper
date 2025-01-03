![logo.png](docs/images/logo.png)

[![Supported Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue)]()
[![Windows](https://github.com/TheMariday/MariMapper/actions/workflows/test_windows.yml/badge.svg)](https://github.com/TheMariday/MariMapper/actions/workflows/test_windows.yml)
[![Ubuntu](https://github.com/TheMariday/MariMapper/actions/workflows/test_ubuntu.yml/badge.svg)](https://github.com/TheMariday/MariMapper/actions/workflows/test_ubuntu.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)



### Marimapper uses your webcam to map addressable LEDs to 3D space!

![](docs/images/reconstruct_with_normals_and_strips.png)

Above example data folder can be found under [docs/highbeam_example/](docs/highbeam_example)

> [!CAUTION]
> [This tool does not support Python 3.12](https://github.com/TheMariday/marimapper/issues/27) or [OS X](https://github.com/TheMariday/marimapper/issues/51)

## Step 0: Install

```shell
pip --version # Ensure that it is //not// python 3.12, see above
pip install pipx
pipx ensurepath
pipx install "git+https://github.com/themariday/marimapper"
```

If you have Python 3.12 installed, install 3.11 and add `--python /path/to/python3.11` to the above `pipx install` command 

[PIPx not working](https://github.com/TheMariday/marimapper/issues/42)? You can also download this repo and run `pip install .` from inside it!

You can run the scripts anywhere by just typing them into a console

## Step 1: Test your camera

> [!TIP]
> use `--help` for any MariMapper command to show a full list of additional arguments! 
> 
> Some not even in this doc...

Run `marimapper_check_camera` to ensure your camera is compatible with MariMapper, or check the list below:

- HP 4310 (settings may not revert)
- Logitech C920
- Dell Latitude 5521 built-in
- HP Envy x360 built-in 

If your camera works, please drop me a line, so I can add it to the list!


Test LED identification by turning down the lights and holding a torch or led up to the camera.

This should start with few warnings, no errors and produce a **very** dark image
with a single crosshair on centered on your LED.

Wrong webcam? MariMapper tools use `--device 0` by default, use `--device 1` to switch to your second webcam.

![alt text](docs/images/camera_check.png "Camera Check window")


> [!TIP]
> If the image is still too bright or uoi can't see a crosshair on your LED, try dimming the lights and playing around with:
> 
> - `--exposure` - The lower the darker, defaults to `-10`, my webcam only goes down to `-11`
> - `--threshold` - The lower the more detections, ranges between `0-255`,  defaults to `128`
## Step 2: Choose your backend

For the Marimapper to communicate with your leds, it requires a backend.

Please see below for documentation on how to run the following backends:

- [FadeCandy](https://github.com/TheMariday/marimapper/tree/main/docs/backends/FadeCandy.md)
- [WLED](https://github.com/TheMariday/marimapper/tree/main/docs/backends/WLED.md)
- [FCMega](https://github.com/TheMariday/marimapper/tree/main/docs/backends/FCMEGA.md)
- [PixelBlaze](https://github.com/TheMariday/marimapper/tree/main/docs/backends/PixelBlaze.md)

If your LED backend isn't supported, you need to write your own, 
[it's super simple](https://github.com/TheMariday/marimapper/tree/main/docs/backends/custom.md)!

## Step 3: Setup your scene

🪨 Make sure that your camera is stable and won't move, try mounting it on a tripod if you can

💡 Make sure there are no light sources in your cameras view, tape up power leds and notification lights

✋ Make sure you can move your camera around without changing the layout of your leds, 
even a small nudge can throw off the reconstructor!

## Step 4: [It's time to thunderize!](https://youtu.be/-5KJiHc3Nuc?t=121)

In a new folder, run `marimapper --backend fadecandy`

and change `fadecandy` to whatever backend you're using and use `--help` to show more options

Set up your LEDs so most of them are in view and when you're ready, type `y` when prompted with `Start scan? [y/n]`

This will turn each LED on and off in turn, **do not move the camera or leds during capture!**

If you just want a 2D map, this is where you can stop!

Rotate your leds or move your webcam to a new position

> [!TIP]
> As long as some of your leds are mostly in view, you can move your webcam to wherever you like!
> Try and get at least 3 views between 6° - 20° apart

Once you have a few views and the reconstructor succeeds, a new window will appear showing the reconstructed 3D positions of your LEDs.

If the window doesn't appear after 4 scans, then something has gone horribly wrong. Delete the scan .csv files in the current working directory and try again.

If it doesn't look quite right, add some more scans!

Here is an example reconstruction of a test tube of LEDs I have

![](docs/images/live_example.png)


### How to move the model around

- Click and drag to rotate the model around. 
- Hold shift to roll the camera
- Use the scroll wheel to zoom in / out
- Use the `n` key to hide / show normals
- Use the `+` / `-` keys to increase / decrease point sizes
- Use `1`, `2`, `3` & `4` keys to change colour scheme

### LED Colors:
By default (`1`), the colors of the leds in the visualiser are as follows:

- Green: Reconstructed
- Blue: Interpolated

# Not working?

Make sure you've read this readme all the way through and do give those error messages a good read too.

They should be able to tell you at least roughly what area is going wrong.

If you want a lot more reading material, run `marimapper` with `-v` to put it into verbose mode.
This will tell you pretty much everything marimapper is doing under the hood.
Also good if you're just curious as to why *x* is taking so long!

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
