# L3D LED Mapper
This is a selection of tools to map LEDs into 3D space using only your webcam

# Tutorial:

## Step 0: Install requirements
pip install -r requirements.txt

## Step 1: Run the camera checker
Run `python scripts/camera_check.py`

## Step 2: Write your LED interface
Everyone's LED systems are different, so I've left it down to you how you talk to you LED's

Add your code to the `backends/custom_backend.py` file before running the next step or checkout the existing backends in the `backends` folder

## Step 3: Run the LED checker
Run `python scripts/led_check.py`
This checks that your backend is working properly and benchmarks the led update speed which is needed for the next step.

## Step 4: Capture a sequence
Set up your leds infront of your camera and run `python scripts/capture_sequence.py`
This will iterate through all your LEDs and register their coordinates in the camera.

## Step 5: Reconstruct
Time to Thunderize!

Run `python scripts/reconstruct.py` to reconstruct your LEDs in 3D space, this may take a while

## Step 6: Lets see what we've got!

Run `python scripts/visualise.py` to visualise your reconstruction.

If there are parts missing, you can re-run step 4 to capture missing areas