import requests


class Backend:

    def __init__(self, wled_base_url="4.3.2.1"):
        self.state_endpoint = f"http://{wled_base_url}/json/state"
        self.info_endpoint = f"http://{wled_base_url}/json/info"
        self.reset_wled()

    def get_led_count(self):

        # Send the HTTP GET request to WLED info API
        response = requests.get(self.info_endpoint)

        # Get the LED Count straight from the WLED Device :D
        if response.status_code != 200:
            raise ConnectionError(f"Failed to retrieve LED count. Status code: {response.status_code}")

        info_data = response.json()
        return info_data['leds']['count']

    def reset_wled(self):

        # Set all the LED's to black on launch
        payload = {"seg": [{"start": 0, "stop": self.get_led_count(), "sel": True}, {"stop": 0}]}

        # Send the HTTP POST request to WLED API
        response = requests.post(self.state_endpoint, json=payload)

        # Check if the request was successful (HTTP status code 200)
        if response.status_code != 200:
            raise ConnectionError(f"Failed to retrieve LED count. Status code: {response.status_code}")
        [self.set_led(i, False) for i in range(self.get_led_count())]

    def set_led(self, led_index: int, on: bool):

        payload = {"seg": {"i": [led_index, "FFFFFF" if on else "000000"]}}

        # Send the HTTP POST request to WLED API
        response = requests.post(self.state_endpoint, json=payload)

        # Check if the request was successful (HTTP status code 200)
        if response.status_code != 200:
            raise ConnectionError(f"WLED Backend failed to set LED state. Status code: {response.status_code}")
