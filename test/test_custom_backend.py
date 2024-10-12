import pytest
import tempfile

from marimapper.utils import load_custom_backend


def test_basic_usage():

    temp_backend_file = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
    temp_backend_file.write(
        b"""
class Backend:

    def __init__(self):
        pass

    def get_led_count(self) -> int:
        return 1

    def set_led(self, led_index: int, on: bool) -> None:
        pass
"""
    )
    temp_backend_file.close()
    backend = load_custom_backend(temp_backend_file.name)

    assert backend.get_led_count() == 1


def test_invalid_backend():
    temp_backend_file = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
    temp_backend_file.write(
        b"""
class Backend:

        def __init__(self):
            pass

        def get_leds(self) -> int: # Should be get_led_count()
            return 1

        def set_led(self, led_index: int, on: bool) -> None:
            pass
    """
    )
    temp_backend_file.close()

    with pytest.raises(RuntimeError):
        load_custom_backend(temp_backend_file.name)
