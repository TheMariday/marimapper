import serial
import struct
import serial.tools.list_ports
from multiprocessing import get_logger

logging = get_logger()


class FCMega:
    DATA_MODE = 1
    UPDATE_MODE = 2

    def __init__(self, port=None):

        self.serial = None

        if port is None:
            port = self._get_port()
            if port is None:
                raise RuntimeError("Cannot find FC Mega")

        self.serial = serial.Serial(port)
        if not self.serial.is_open:
            raise RuntimeError("Cannot open port")

    def _get_port(self):
        for device in serial.tools.list_ports.comports():
            if device.serial_number.startswith("FCM"):
                logging.info(f"found port {device.name}")
                return device.name

        return None

    def set_pixels(self, pixels, offset=0):
        update_buffer = struct.pack("<BHH", self.DATA_MODE, offset, len(pixels))
        for led in pixels:
            update_buffer += struct.pack("BBB", led[0], led[1], led[2])
        self.serial.write(update_buffer)

        buffer_update_response = struct.unpack("<B", self.serial.read(1))[0]

        return buffer_update_response == 1

    def update(self):

        self.serial.write(struct.pack("<B", self.UPDATE_MODE))
        update_response = struct.unpack("<B", self.serial.read(1))[0]

        return update_response == 1
