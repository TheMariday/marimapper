from multiprocessing import get_logger
import pixelblaze

logger = get_logger()


class Backend:

    def __init__(self, pixelblaze_ip="4.3.2.1"):
        self.pb = pixelblaze.Pixelblaze(pixelblaze_ip)
        self.pb.setActivePatternByName(
            "marimapper"
        )  # Need to install marimapper.js to your pixelblaze

    def get_led_count(self):
        pixel_count = self.pb.getPixelCount()
        logger.info(f"Pixelblaze reports {pixel_count} pixels")
        return pixel_count

    def set_led(self, led_index: int, on: bool):
        self.pb.setActiveVariables({"pixel_to_light": led_index, "turn_on": on})

    def set_map_coordinates(self, pixelmap: list):
        result = self.pb.setMapCoordinates(pixelmap)
        if result is False:
            raise RuntimeError("Pixelblaze Backend failed to upload map coordinates.")
        self.pb.wsSendJson({"mapperFit": 0})

    def set_current_map(self, pixelmap_name: str):
        self.pb.setActivePatternByName(pixelmap_name)
