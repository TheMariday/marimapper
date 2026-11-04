import argparse
from base64 import urlsafe_b64encode
from functools import partial
from hashlib import sha256
import os
from urllib.parse import urlsplit

import requests


def pixlite_backend_set_args(parser):
    parser.add_argument(
        "--server", required=True, help="PixLite host or HTTPS controller URL"
    )


def pixlite_backend_factory(args: argparse.Namespace):
    return partial(Backend, args.server)


class PixLiteRequestError(RuntimeError):
    """The controller explicitly rejected a request."""


class Backend:
    """Use PixLite Mk3 test-data mode to illuminate one physical pixel at a time."""

    def __init__(self, server: str):
        base_url = server if "://" in server else f"http://{server}"
        url = urlsplit(base_url)
        if (
            url.scheme not in ("http", "https")
            or not url.hostname
            or url.username is not None
            or url.path not in ("", "/")
            or url.query
            or url.fragment
        ):
            raise ValueError("Specify a PixLite hostname, IP address or controller URL")

        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/v1.9/?user=admin"
        self.in_test_mode = False
        version = self._request("version")
        if version["prodFamilyName"] != "PixLite Mk3" or not any(
            api["maj"] == "v1" and api["min"][0] <= 9 <= api["min"][1]
            for api in version["apiVer"]
        ):
            raise RuntimeError("PixLite Mk3 with API v1.9 is required")

        if version["authReqd"]:
            password = os.environ.get("PIXLITE_PASSWORD")
            if url.scheme != "https" or not password:
                raise RuntimeError(
                    "A password-protected PixLite requires an HTTPS URL and PIXLITE_PASSWORD"
                )
            digest = urlsafe_b64encode(sha256(password.encode("utf-8")).digest())
            self.api_url += f"&auth={digest.decode('ascii').rstrip('=')}"

        config = self._request(
            "configRead",
            {
                "path": [
                    "pix.colorType",
                    "pix.expand",
                    "pixPort.pixCount",
                    "pixPort.nullPix",
                    "pixPort.group",
                ]
            },
        )["config"]
        constants = self._request("constantRead", {"path": ["dev.pixPorts"]})[
            "constant"
        ]
        port_count = constants["dev"]["pixPorts"] * (
            2 if config["pix"]["expand"] else 1
        )
        ports = config["pixPort"]
        if any(
            len(ports[key]) < port_count for key in ("pixCount", "nullPix", "group")
        ):
            raise RuntimeError(
                "PixLite returned an incomplete pixel port configuration"
            )

        self.counts = []
        self.unverified_ports = set()
        for index in range(port_count):
            count = ports["pixCount"][index]
            if count == 0:
                self.counts.append(0)
                continue
            null = ports["nullPix"][index]
            group = ports["group"][index]
            if not 0 <= null <= count or not 1 <= group <= count:
                raise RuntimeError(
                    f"PixLite port {index + 1} has invalid pixel settings"
                )
            logical_count = (count - null + group - 1) // group
            self.counts.append(logical_count)
            if logical_count and (null or group > 1):
                self.unverified_ports.add(index + 1)
        if not self.get_led_count():
            raise RuntimeError("PixLite has no scannable pixels")
        channels = {"RGB": 3, "RGBW": 4, "RGBWX": 5}
        self.color_channels = channels[config["pix"]["colorType"]]

    def _request(self, name: str, params: dict | None = None) -> dict:
        try:
            if name == "version":
                response = requests.get(
                    f"{self.base_url}/ver", timeout=3, allow_redirects=False
                )
            else:
                payload = {"req": name, "id": 1}
                if params is not None:
                    payload["params"] = params
                response = requests.post(
                    self.api_url, json=payload, timeout=3, allow_redirects=False
                )
            if response.status_code != 200:
                raise RuntimeError(
                    f"PixLite {name} returned HTTP {response.status_code}"
                )
            body = response.json()
        except (requests.RequestException, ValueError):
            raise RuntimeError(
                f"PixLite {name} failed or returned invalid JSON"
            ) from None
        if (
            not isinstance(body, dict)
            or body.get("resp") != name
            or (name != "version" and body.get("id") != 1)
        ):
            raise RuntimeError(f"PixLite returned an invalid {name} reply")
        error = body.get("err")
        if isinstance(error, dict):
            raise PixLiteRequestError(
                f"PixLite rejected {name} (code {error.get('code')})"
            )
        if not isinstance(body.get("result"), dict):
            raise RuntimeError(f"PixLite returned no result for {name}")
        return body["result"]

    def get_led_count(self) -> int:
        return sum(self.counts)

    def _set_color(self, port: int, pixel: int, on: bool) -> None:
        was_in_test_mode = self.in_test_mode
        if not was_in_test_mode:
            status = self._request("statusRead", {"path": ["mode"]})["status"]
            if status["mode"] != "live":
                raise RuntimeError("PixLite must be in live mode before scanning")
            # A request can take effect even if its response is lost.
            self.in_test_mode = True

        color = [64 if on else 0] * 3 + [0] * (self.color_channels - 3)
        try:
            result = self._request(
                "modeTestData",
                {
                    "op": "setColor",
                    "color": color,
                    "colorRes": "8Bit",
                    "pixPortNum": port,
                    "pixNum": pixel,
                },
            )
        except PixLiteRequestError:
            self.in_test_mode = was_in_test_mode
            raise
        if result["status"]["mode"] != "testData":
            raise RuntimeError("PixLite did not enter test-data mode")

    def set_led(self, led_index: int, on: bool) -> None:
        if not 0 <= led_index < self.get_led_count():
            raise IndexError(f"PixLite LED index out of range: {led_index}")
        for port, count in enumerate(self.counts, start=1):
            if led_index < count:
                if port in self.unverified_ports:
                    raise RuntimeError(
                        f"PixLite port {port} uses null pixels or grouping, "
                        "which still needs test-mode address verification"
                    )
                self._set_color(port, led_index + 1, on)
                return
            led_index -= count

    def blackout(self) -> None:
        self._set_color(0, 0, False)

    def close(self) -> None:
        if self.in_test_mode:
            result = self._request("modeLive")
            if result["status"]["mode"] != "live":
                raise RuntimeError("PixLite did not return to live mode")
            self.in_test_mode = False
