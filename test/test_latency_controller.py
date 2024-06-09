from lib.latency_controller import LatencyController


def test_latency_controller_with_not_enough_samples():
    default_latency = 1.0
    lc = LatencyController(default_latency_sec=default_latency)
    [lc.add_latency(i) for i in range(9)]

    assert lc.latency == default_latency


def test_latency_controller_basic():

    latencies = [0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 1.0]

    lc = LatencyController(percentile=90, multiplier=1.0)

    [lc.add_latency(latency) for latency in latencies]

    assert lc.latency < 0.3


def test_latency_controller_rolling_buffer():

    latencies = [1000, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2]

    lc = LatencyController(
        sample_size_max=len(latencies) - 1, percentile=90, multiplier=1.0
    )

    [lc.add_latency(latency) for latency in latencies]

    assert lc.latency == 0.2
