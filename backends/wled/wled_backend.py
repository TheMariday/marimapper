import requests


class Backend:

    def __init__(self, wled_base_url="1.2.3.4"):
        self.wled_base_url = wled_base_url
        self.led_count = self.get_led_count()

    def get_led_count(self):
        # Construct the WLED info API endpoint
        info_endpoint = f"http://{self.wled_base_url}/json/info"

        # Send the HTTP GET request to WLED info API
        response = requests.get(info_endpoint)

        # Get the LED Count straight from the WLED Device :D
        if response.status_code != 200:
            raise ConnectionError(f"Failed to retrieve LED count. Status code: {response.status_code}")

        info_data = response.json()
        return info_data['leds']['count']

    def set_led(self, led_index: int, on: bool):
        # Construct the WLED API endpoint
        endpoint = f"http://{self.wled_base_url}/json/state"

        payload = {"seg": {"i": [led_index, "FFFFFF" if on else "000000"]}}

        # Send the HTTP POST request to WLED API
        response = requests.post(endpoint, json=payload)

        # Check if the request was successful (HTTP status code 200)
        if response.status_code != 200:
            raise ConnectionError(f"WLED Backend failed to set LED state. Status code: {response.status_code}")
