from marimapper.led import (
    LED3D,
    remove_duplicates,
    fill_gaps,
    get_led,
    LEDState,
    get_next,
    LED2D,
    last_view,
    Point2D,
)


def test_remove_duplicates():

    led_0 = LED3D(0)
    led_0.point.set_position(0, 0, 0)
    led_1 = LED3D(0)
    led_0.point.set_position(1, 0, 0)

    removed_duplicates = remove_duplicates([led_0, led_1])

    assert len(removed_duplicates) == 1

    merged_pos = removed_duplicates[0].point.position
    assert merged_pos[0] == 0.5
    assert merged_pos[1] == 0
    assert merged_pos[2] == 0


def test_fill_gaps():

    led_0 = LED3D(0)
    led_0.point.set_position(0, 0, 0)
    led_6 = LED3D(6)
    led_6.point.set_position(6, 0, 0)

    leds = [led_0, led_6]
    fill_gaps(leds)

    assert len(leds) == 7

    for led_id in range(7):
        assert get_led(leds, led_id).point.position[0] == led_id


def test_get_color():

    led = LED3D(0)

    assert led.get_color() == (0, 255, 0)

    interpolated_led = LED3D(0)
    interpolated_led.add_state(LEDState.INTERPOLATED)

    assert interpolated_led.get_color() == (0, 255, 255)

    merged_led = LED3D(0)
    merged_led.add_state(LEDState.MERGED)

    assert merged_led.get_color() == (0, 255, 255)


def test_get_led():
    leds = [LED3D(0), LED3D(1), LED3D(2)]

    assert get_led(leds, 0) == leds[0]

    assert get_led(leds, 2) == leds[2]

    assert get_led(leds, 5) is None


def test_get_next():

    led_1 = LED3D(led_id=1)
    led_2 = LED3D(led_id=2)
    led_3 = LED3D(led_id=3)
    led_5 = LED3D(led_id=5)

    leds = [led_5, led_3, led_2, led_1]

    assert get_next(led_1, leds) == led_2
    assert get_next(led_5, leds) is None
    assert get_next(led_2, leds) == led_3


def test_last_view():
    led_1 = LED2D(led_id=1, view_id=1, point=Point2D(0.0, 0.0))
    led_2 = LED2D(led_id=2, view_id=2, point=Point2D(0.0, 0.0))

    assert last_view([led_1, led_2]) == 2
