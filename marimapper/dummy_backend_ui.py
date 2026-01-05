class Backend:

    def __init__(self):
        pass

    def connected(self):
        return False

    def state(self):
        return "Not a valid backend"

class BackendUI:
    name = "None"
    def __init__(self):
        self.backend = Backend()

    def remove(self):
        pass

    def enable(self):
        pass

    def disable(self):
        pass

    def get_backend(self):
        return self.backend