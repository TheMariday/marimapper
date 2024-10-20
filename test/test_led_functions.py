from marimapper.led import LED3D, remove_duplicates


def test_remove_duplicates():

    led_0 = LED3D(0)
    led_0.point.position = (0, 0, 0)
    led_1 = LED3D(0)
    led_0.point.position = (1, 0, 0)

    removed_duplicates = remove_duplicates([led_0, led_1])

    assert len(removed_duplicates) == 1

    merged_pos = removed_duplicates[0].point.position
    assert merged_pos[0] == 0.5
    assert merged_pos[1] == 0
    assert merged_pos[2] == 0
