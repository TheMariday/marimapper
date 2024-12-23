import pytest
import tempfile

from marimapper.utils import get_backend


def test_basic_usage():

    temp_backend_file = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
    temp_backend_file.write(
        b"""
class Backend:

    def __init__(self):
        pass

    def get_led_count(self):
        return 1

    def set_led(self, led_index, on):
        pass
"""
    )
    temp_backend_file.close()
    backend = get_backend(temp_backend_file.name)

    assert backend.get_led_count() == 1


def test_invalid_backend_due_to_missing_function():
    temp_backend_file = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
    temp_backend_file.write(
        b"""
class Backend:

        def __init__(self):
            pass

        def get_leds(self): # Should be get_led_count()
            return 1

        def set_led(self, led_index, on):
            pass
    """
    )
    temp_backend_file.close()

    with pytest.raises(RuntimeError):
        get_backend(temp_backend_file.name)


def test_invalid_backend_due_to_missing_function_arguments():
    temp_backend_file = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
    temp_backend_file.write(
        b"""
class Backend:

        def __init__(self):
            pass

        def get_led_count(self) -> int:
            return 1

        def set_led(self, led_index): # this is missing the on parameter
            pass
    """
    )
    temp_backend_file.close()

    with pytest.raises(RuntimeError):
        get_backend(temp_backend_file.name)


def test_fadecandy(monkeypatch):

    from marimapper.backends.fadecandy import opc

    def get_client_patch(uri):
        class ClientPatch:
            def put_pixels(self, _):
                pass

        return ClientPatch()

    monkeypatch.setattr(opc, "Client", get_client_patch)

    get_backend("fadecandy")
    get_backend("fadecandy", "1.2.3.4")


def test_wled(monkeypatch):

    import requests

    def return_response_patch(*arg, **kwargs):
        class ResponsePatch:
            status_code = 200

            def json(self):
                return {"leds": {"count": 1}}

        return ResponsePatch()

    monkeypatch.setattr(requests, "post", return_response_patch)
    monkeypatch.setattr(requests, "get", return_response_patch)

    get_backend("wled")
    get_backend("wled", "1.2.3.4")


def test_fcmega(monkeypatch):

    import serial.tools.list_ports

    class SerialPatch:

        def __init__(self, _):
            self.is_open = True

        def write(self, _):
            pass

        def read(self, _):
            return b"1"

    def comports_patch():
        class ComportPatch:
            serial_number = "FCM000"
            name = "10"

        return [ComportPatch()]

    monkeypatch.setattr(serial, "Serial", SerialPatch)
    monkeypatch.setattr(serial.tools.list_ports, "comports", comports_patch)

    get_backend("fcmega")


# py_mini_racer uses import pkg_resources which is depreciated
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_pixelblaze(monkeypatch):

    import pixelblaze

    class PixelblazePatch:
        def __init__(self, _):
            pass

        def setActivePatternByName(self, _):
            pass

        def getPixelCount(self):
            return 1

    monkeypatch.setattr(pixelblaze, "Pixelblaze", PixelblazePatch)

    get_backend("pixelblaze", "1.2.3.4")


def test_invalid_backend():

    with pytest.raises(RuntimeError):
        get_backend("invalid_backend")

def test_dummy_backend():

    dummy = get_backend("dummy")
    assert dummy.get_led_count() == 0
