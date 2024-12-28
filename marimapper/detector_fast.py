from marimapper.camera import Camera
from marimapper.detector import show_image
from marimapper.timeout_controller import TimeoutController
from marimapper.queues import Queue2D
import logging
from multiprocessing import get_logger
import numpy as np
import time
import cv2

from marimapper.utils import backend_black


logger = get_logger()

def get_binary_length(led_id:int) -> int:
    return len(bin(led_id)[2:])

def led_id_to_binary(led_id:int, binary_length:int) -> list[int]:

    binary_as_text = bin(led_id)[2:]
    binary_as_bool = [int(v) for v in binary_as_text]

    binary_padded = [0 for _ in range(binary_length)]

    binary_padded[-len(binary_as_bool):] = binary_as_bool

    return binary_padded



def detect_leds_fast(
    led_id_from: int,
    led_id_to: int,
    cam: Camera,
    led_backend,
    view_id: int,
    timeout_controller: TimeoutController,
    threshold: int,
    display: bool,
    output_queues: list[Queue2D],
):

    # this isn't very smart if the led_id_from is non zero, oh well
    binary_length = get_binary_length(led_id_to)

    images = []

    # woah led0 is 0,0,0,0,0. nope
    led_binaries = [led_id_to_binary(led_id, binary_length) for led_id in range(led_id_to)]

    for binary_index in range(binary_length):
        print(f"binary index {binary_index}")
        if False:
            buffer = [[255,255,255] if led_binaries[led_id][binary_index] else [0,0,0] for led_id in range(led_id_to)]
            led_backend.set_leds(buffer)
            # set backend
            cam.eat()
            image = cam.read()
            if display:
                show_image(image)

            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) / 255.0
            images.append(image)
            np.save(f"bin_{binary_index}", image)
        else:
            image = np.load(f"bin_{binary_index}.npy")
            image[0:240, :] = 0.0
            # cv2.imwrite(f"bin_{binary_index}.png", image*255)
            images.append(image)

            # cv2.imshow("image", image)
            # cv2.waitKey(0)

    backend_black(backend)

    for led_id in range(led_id_to):
        mat = 1
        for binary_index in range(binary_length):
            if led_binaries[led_id][binary_index]:
                mat = images[binary_index] * mat
            else:
                mat = (1.0 - images[binary_index]) * mat

            # print(f"{led_id} {binary_index}")
            # _, mat_max, _, mat_max_loc = cv2.minMaxLoc(mat)
            # disp = mat.copy()
            # cv2.drawMarker(disp, mat_max_loc, 1.0)
            # cv2.imshow(f"t{binary_index}", disp)


        _, mat_max, _, mat_max_loc = cv2.minMaxLoc(mat)
        responses = [float(i[mat_max_loc[1], mat_max_loc[0]]) for i in images]
        min_response = min(responses)
        #print(f"{led_id} {mat_max} {mat_max_loc[0]} {mat_max_loc[1]}", *led_binaries[led_id], *responses)
        print(f"{led_id} {min_response}")
        # if mat_max > 0.3:
        #     pass
        cv2.waitKey(0)

    # find a map between led_id to binary number

    # for binary_index in len(binary):
        # wait for black
        # push buffer
        # wait for white
        # capture image either way and save it

    # for led in led range:
        # mul the maps together
        # run standard detection with a minute threshold
        # push to output queue75


    # send it


if __name__ == "__main__":

    from marimapper.backends.fcmega import fcmega_backend

    logger.setLevel(logging.DEBUG)

    cam = Camera(0)

    cam.set_exposure(-10)

    backend = fcmega_backend.Backend()

    timeout_controller = TimeoutController()



    detect_leds_fast(0, 400, cam, backend, 0, timeout_controller, 128, True, [])

    time.sleep(1)