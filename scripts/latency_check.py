import argparse
import math
import sys
sys.path.append('./')
from lib import utils
from lib import L3D
from lib.color_print import cprint, Col
import time
import numpy as np

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Tests the functionality and latency of your LED backend')

    parser.add_argument("--backend", type=str, help="The backend used for led communication",
                        choices=["custom", "fadecandy", "wled", "lcm"], default="custom")

    parser.add_argument("--reference_led", type=int,
                        help="This is the index of the LED should be visible from the camera", default=0)

    utils.add_camera_args(parser)

    args = parser.parse_args()

    cprint(f"Loading {args.backend} backend")

    led_count = args.reference_led + 1

    led_backend = utils.get_backend(args.backend, led_count)

    led_backend.set_led(args.reference_led, False)

    l3d = L3D.L3D(args.device, args.exposure, args.threshold, width=args.width, height=args.height)

    #  wait for 1 seconds for the backend to update, we don't know the latency at this point
    time.sleep(1)

    result = l3d.find_led()
    if result is not None:
        cprint(f"All LEDs should be off, however LED has been detected at {result.center},"
               f" please run camera_check to ensure the detector is working properly", Col.FAIL)
        quit()

    cprint("Testing average latency...")

    latencies = []

    for _ in range(100):
        # Set reference led to off and spin until L3D can't find the led anymore
        led_backend.set_led(args.reference_led, False)
        while l3d.find_led() is not None:
            pass
        # Set reference led to on and see how long it takes for L3D to find it
        led_update_time = time.time()
        led_backend.set_led(args.reference_led, True)
        while l3d.find_led() is None:
            pass
        latencies.append(time.time() - led_update_time)

    #  remove the first few as they tend to be off
    latencies = latencies[2:]

    # Destroy l3d so the logging doesn't get in the way
    del l3d

    min_ms = math.floor(min(latencies) * 1000)
    avg_ms = round((sum(latencies) / len(latencies)) * 1000)
    max_ms = math.ceil(max(latencies) * 1000)

    cprint(f"Latency Min: {min_ms}ms", Col.BLUE)
    cprint(f"Latency Avg: {avg_ms}ms", Col.BLUE)
    cprint(f"Latency Max: {max_ms}ms", Col.BLUE)

    suggested_latency = round((np.percentile(latencies, 95) * 1.1) * 1000)

    cprint(f"Suggested latency value for 95% of cases + 10%: {suggested_latency}ms", Col.BLUE)
