from marimapper.led import LED3D, remove_duplicates, fill_gaps, get_led


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
