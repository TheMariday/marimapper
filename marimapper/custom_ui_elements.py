from typing import Tuple

import viser
import numpy as np
import cv2

from ui_style import Color

class ButtonProgressWrapper:

    def __init__(self, button:viser.GuiButtonHandle, in_progress_message="waiting"):
        self.button = button
        self.button_label_original = button.label
        self.button_label_progress = in_progress_message

    def __enter__(self):
        self.button.disabled = True
        self.button.label = self.button_label_progress

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.button.disabled = False
        self.button.label = self.button_label_original

class ProgressWrapper:

    def __init__(self, *args):
        self.things = args

    def __enter__(self):
        for thing in self.things:
            thing.disabled = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        for thing in self.things:
            thing.disabled = False

class CustomProgress:

    def __init__(self, gui, led_min, led_max):

        self.image = gui.add_image(np.zeros((64,640,3)))
        self.range = range(led_min,led_max)
        self.data = {}
        self.update()

    def set(self, index, success):
        self.data[index] = success
        self.update()

    def reset(self):
        self.data = {}
        self.update()

    def update(self):
        width = self.range.stop - self.range.start
        image_np = np.ones((1,width,3),dtype=np.uint8) * 128
        for i in self.range:
            if i in self.data:
                if self.data[i]:
                    image_np[:, i - self.range.start] = Color.YES
                else:
                    image_np[:, i - self.range.start] = Color.WARNING

            if i%2:
                image_np[:, i - self.range.start] = image_np[:, i - self.range.start] * 0.8


        self.image.image = cv2.resize(image_np, (640,32), interpolation=cv2.INTER_NEAREST)

    def set_range(self, range_min, range_max):
        self.range = range(range_min,range_max)
        self.update()



def get_confirmation(client, message, yes_lambda, no_lambda=None,  color=Color.DEFAULT):

    with client.gui.add_modal(message) as modal:
        client.gui.add_image(cv2.imread("C:\\Users\\marti\\Downloads\\1395867442.akliasin_murr.png"))
        client.gui.add_button("Yes", color=Color.YES).on_click(lambda _: on_click(True))
        client.gui.add_button("No", color=Color.NO).on_click(lambda _: on_click(False))

        def on_click(confirmed):
            modal.close()
            if confirmed:
                if yes_lambda:
                    yes_lambda()
            else:
                if no_lambda:
                    no_lambda()


def notify(clients, message:str, notification:bool=True, modal:bool=False, color:Tuple[int,int,int]=Color.DEFAULT):

    if isinstance(clients, viser.ClientHandle):
        clients = [clients]

    for client in clients:
        if notification:
            client.add_notification(message, body="", auto_close_seconds=5, color=color)
        if modal:
            with client.gui.add_modal(message) as modal:
                client.gui.add_image(cv2.imread("C:\\Users\\marti\\Downloads\\1395867442.akliasin_murr.png"))
                client.gui.add_button("Ok", color=Color.CONFIRM).on_click(lambda _: modal.close())

