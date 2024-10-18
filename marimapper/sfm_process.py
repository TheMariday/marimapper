from multiprocessing import Process, Event
from marimapper.led import LED2D, rescale, recenter
from marimapper.sfm import sfm


class SFM(Process):

    def __init__(
        self, led_map_2d_queue=None, led_map_3d_queue=None, rescale=True, recenter=True
    ):
        super().__init__()
        self.exit_event = Event()
        self.led_map_3d_queue = led_map_3d_queue
        self.led_map_2d_queue = led_map_2d_queue
        self.rescale = rescale
        self.recenter = recenter
        self.leds: list[LED2D] = []

    def shutdown(self):
        self.exit_event.set()

    def run(self):

        update_required = False

        while not self.exit_event.is_set():
            if self.led_map_2d_queue.empty():

                if not update_required:
                    continue

                leds_3d = sfm(self.leds)

                if len(leds_3d) == 0:
                    continue

                if self.rescale:
                    rescale(leds_3d)
                if self.recenter:
                    recenter(leds_3d)

                self.led_map_3d_queue.put(leds_3d)
                update_required = False
            else:
                led = self.led_map_2d_queue.get()
                self.leds.append(led)
                update_required = True
