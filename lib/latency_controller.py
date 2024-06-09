import numpy as np


class LatencyController:

    def __init__(
        self,
        sample_size_min=10,
        sample_size_max=20,
        default_latency_sec=1.0,
        percentile=90,
        multiplier=1.5,
    ):
        self._latencies = []
        self._sample_size_min = sample_size_min
        self._sample_size_max = sample_size_max
        self._percentile = percentile
        self._multiplier = multiplier
        self.latency = default_latency_sec

    def add_latency(self, latency):
        self._latencies.append(latency)
        self._latencies = self._latencies[-self._sample_size_max :]

        self.update_latency()

    def update_latency(self):
        if len(self._latencies) >= self._sample_size_min:
            self.latency = (
                np.percentile(self._latencies, self._percentile) * self._multiplier
            )
