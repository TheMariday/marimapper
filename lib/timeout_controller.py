import numpy as np


class TimeoutController:

    def __init__(
        self,
        sample_size_min=10,
        sample_size_max=20,
        default_timeout_sec=1.0,
        percentile=90,
        multiplier=1.5,
    ):
        self._response_times = []
        self._sample_size_min = sample_size_min
        self._sample_size_max = sample_size_max
        self._percentile = percentile
        self._multiplier = multiplier
        self.timeout = default_timeout_sec

    def add_response_time(self, response_time):
        self._response_times.append(response_time)
        self._response_times = self._response_times[-self._sample_size_max :]

        self.update_timeout()

    def update_timeout(self):
        if len(self._response_times) >= self._sample_size_min:
            self.timeout = (
                np.percentile(self._response_times, self._percentile) * self._multiplier
            )
