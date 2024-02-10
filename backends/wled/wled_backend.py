import requests

wled_ip = "1.2.3.4"  # Replace with the actual IP address or hostname of your WLED device


class Backend:

    def __init__(self, wled_base_url):
        self.wled_base_url = wled_base_url
        self.led_count = self.get_led_count()

    def get_led_count(self):
        # Construct the WLED info API endpoint
        info_endpoint = f"http://{wled_ip}/json/info"

        try:
            # Send the HTTP GET request to WLED info API
            response = requests.get(info_endpoint)

            # Get the LED Count straight from the WLED Device :D
            if response.status_code == 200:
                info_data = response.json()
                return info_data['leds']['count']
            else:
                print(f"Failed to retrieve LED count. Status code: {response.status_code}")
                return 0
        except Exception as e:
            print(f"Error: {e}")
            return 0

    def set_led(self, led_index: int, on: bool):
        # Construct the WLED API endpoint
        endpoint = f"http://{wled_ip}/json/state"

        # Not the cleanest, but its honest work :3c
        if on is True:
            payload = {"seg": {"i": [led_index, "FFFFFF"]}}
        else:
            payload = {"seg": {"i": [led_index, "000000"]}}

        try:
            # Send the HTTP POST request to WLED API
            response = requests.post(endpoint, json=payload)

            # Check if the request was successful (HTTP status code 200)
            if response.status_code == 200:
                print(f"LED at index {led_index} {'turned on' if on else 'turned off'} successfully.")
            else:
                print(f"Failed to set LED state. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error: {e}")


backend = Backend(wled_base_url=wled_ip)
print(f"LED count: {backend.led_count}")
