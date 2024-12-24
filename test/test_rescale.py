from marimapper.led import rescale, LED3D


def test_rescale_basic():

    led_0 = LED3D(0)
    led_1 = LED3D(1)
    led_2 = LED3D(2)

    led_0.point.position[0] = 0
    led_1.point.position[0] = 2
    led_2.point.position[0] = 4

    scale = rescale([led_0, led_1, led_2])

    assert scale == 0.5

    assert led_0.point.position[0] == 0
    assert led_1.point.position[0] == 1
    assert led_2.point.position[0] == 2
