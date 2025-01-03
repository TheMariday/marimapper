# PixelBlaze Backend Tutorial

To use PixelBlaze with marimapper you first need to upload a pattern file to your controller.

You can do this via the web UI by uploading [this file](https://github.com/TheMariday/marimapper/blob/main/marimapper/backends/pixelblaze/marimapper.epe)
as a new pattern.

Once this is done, run `marimapper_check_backend --backend pixelblaze` to test it. It should cause LED 0 to blink.

By default, marimapper tools will use the address `4.3.2.1`, but this can be changed by using the `--server` argument.

Once you've checked your PixelBlaze setup is talking nicely with marimapper, you can go ahead and start mapping!

Once you're done, you can upload your 3D map to pixelblaze by running `marimapper_upload_mapping_to_pixelblaze` 
in the same folder as your `led_map_3d.csv`. 

Don't forget to add the `--server` argument if you've needed to change it in the previous steps

Now you've learnt the PixelBlaze specifics, shoo! Back to the main README.md with you!