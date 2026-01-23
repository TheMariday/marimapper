class MMState:
    def __init__(self, state_change_callback):
        self._backend_connected = False
        self._camera_testing = False
        self._scanning = False
        self._callback = state_change_callback

    def ready(self):
        return not self._scanning and not self._camera_testing and self._backend_connected

    @property
    def backend_connected(self):
        return self._backend_connected

    @backend_connected.setter
    def backend_connected(self, value):
        self._backend_connected = value
        self._callback()

    @property
    def camera_testing(self):
        return self._camera_testing

    @camera_testing.setter
    def camera_testing(self, value):
        self._camera_testing = value
        self._callback()

    @property
    def scanning(self):
        return self._scanning

    @scanning.setter
    def scanning(self, value):
        self._scanning = value
        self._callback()
