from multiprocessing import Process, Event
from marimapper.led import LED2D
from marimapper.sfm import sfm


class SFM(Process):

    def __init__(
        self,
        led_map_2d_queue=None,
        led_map_3d_queue=None,
    ):
        super().__init__()
        self.exit_event = Event()
        self.led_map_3d_queue = led_map_3d_queue
        self.led_map_2d_queue = led_map_2d_queue
        self.leds: list[LED2D] = []

    def shutdown(self):
        self.exit_event.set()

    def run(self):

        update_required = False

        while not self.exit_event.is_set():
            if self.led_map_2d_queue.empty():
                if update_required:
                    print(
                        f"just finished recieving data, trying to build with {len(self.leds)} points"
                    )
                    leds_3d = sfm(self.leds)
                    print(f"reconstructed leds 3D: {len(leds_3d)}")
                    self.led_map_3d_queue.put(leds_3d)
                    update_required = False
            else:
                led = self.led_map_2d_queue.get()
                self.leds.append(led)
                update_required = True
