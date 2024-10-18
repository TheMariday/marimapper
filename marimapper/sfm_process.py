from pathlib import Path
from multiprocessing import Process, Event


from marimapper import logging
from marimapper.sfm import sfm


class SFM(Process):

    def __init__(
        self,
        directory: Path,
        rescale=False,
        interpolate=False,
        event_on_update=None,
        led_map_2d_queue=None,
        led_map_3d_queue=None,
    ):
        logging.debug("SFM initialising")
        super().__init__()
        self.directory = directory
        self.rescale = rescale
        self.interpolate = interpolate
        self.exit_event = Event()
        self.event_on_update = event_on_update
        self.led_map_3d_queue = led_map_3d_queue
        self.led_map_2d_queue = led_map_2d_queue
        self.leds = []

        logging.debug("SFM initialised")

    def add_led_maps_2d(self, maps):
        self.led_map_2d_queue.put(maps)

    def shutdown(self):
        logging.debug("SFM sending shutdown request")
        self.exit_event.set()

    def run(self):
        logging.debug("SFM process starting")

        while not self.exit_event.is_set():
            if self.led_map_2d_queue.empty():
                map_3d = sfm(self.leds)
                self.led_map_3d_queue.put(map_3d)
            else:
                led = self.led_map_3d_queue.get()
                self.leds.append(led)
