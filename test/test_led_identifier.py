import sys
import cv2
sys.path.append('./')
from lib.led_identifier import LedFinder


def close(x, y):
    return abs(x - y) < 0.5


def load_image(filename):
    image = cv2.imread(filename)
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def test_init():
    LedFinder()


def test_basic_image_loading():
    led_finder = LedFinder()

    image = load_image("test/media/capture_sequence/a_0.png")

    led_results = led_finder.find_led(image)

    assert close(led_results.u(), 193)
    assert close(led_results.v(), 150)


def test_none_found():

    led_finder = LedFinder()

    image = load_image("test/media/capture_sequence/a_none.png")

    led_results = led_finder.find_led(image)

    assert led_results is None
