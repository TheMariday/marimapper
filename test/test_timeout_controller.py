from marimapper.timeout_controller import TimeoutController


def test_timeout_controller_with_not_enough_samples():
    default_timeout = 1.0
    tc = TimeoutController(default_timeout_sec=default_timeout)
    [tc.add_response_time(i) for i in range(9)]

    assert tc.timeout == default_timeout


def test_timeout_controller_basic():

    response_times = [0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 1.0]

    tc = TimeoutController(percentile=90, multiplier=1.0)

    [tc.add_response_time(timeout) for timeout in response_times]

    assert tc.timeout < 0.3


def test_timeout_controller_rolling_buffer():

    response_times = [1000, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2]

    tc = TimeoutController(
        sample_size_max=len(response_times) - 1, percentile=90, multiplier=1.0
    )

    [tc.add_response_time(timeout) for timeout in response_times]

    assert tc.timeout == 0.2
