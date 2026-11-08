from functools import partial
import os
from unittest.mock import Mock

import pytest
import requests

from marimapper.backends.pixlite.pixlite_backend import Backend, PixLiteRequestError


@pytest.fixture
def controller(monkeypatch):
    state = {"mode": "live", "commands": [], "counts": [2, 0, 3, 0]}

    def request(self, name, params=None):
        if name == "version":
            return {
                "prodFamilyName": "PixLite Mk3",
                "apiVer": [{"maj": "v1", "min": [0, 9]}],
                "authReqd": False,
            }
        if name == "constantRead":
            return {
                "constant": {
                    "dev": {"pixPorts": state.get("pix_ports", 2)},
                    "pixTypes": [
                        {
                            "pixType": "TestPixel",
                            "colorTypes": state.get(
                                "color_types", ["RGB", "RGBW", "RGBWX"]
                            ),
                            "canExpand": state.get("can_expand", True),
                            "bitRes": state.get("bit_res", 16),
                        }
                    ],
                }
            }
        if name == "configRead":
            return {
                "config": {
                    "pix": {
                        "expand": state.get("expanded", True),
                        "colorType": state.get("color_type", "RGBW"),
                        "pixType": "TestPixel",
                        "inFormat": state.get("in_format", "8Bit"),
                    },
                    "pixPort": {
                        "pixCount": state["counts"],
                        "nullPix": state.get("null_pixels", [0, 0, 0, 0]),
                        "group": state.get("groups", [1, 1, 1, 1]),
                    },
                }
            }
        if name == "modeTestData":
            if state.get("reject"):
                raise PixLiteRequestError("unauthorized")
            state["commands"].append(params)
            state["mode"] = "testData"
            if state.get("timeout"):
                raise RuntimeError("response lost")
        elif name == "modeLive":
            state["mode"] = "live"
        else:
            assert name == "statusRead"
        return {"status": {"mode": state["mode"]}}

    monkeypatch.setattr(Backend, "_request", request)
    return state


def test_expanded_port_mapping_and_blackout(controller):
    backend = Backend("pixlite.local")
    assert backend.get_led_count() == 5
    backend.set_led(1, True)
    backend.set_led(2, True)
    backend.set_led(2, False)
    backend.blackout()
    with pytest.raises(IndexError):
        backend.set_led(5, True)

    commands = controller["commands"]
    assert [(cmd["pixPortNum"], cmd["pixNum"]) for cmd in commands] == [
        (1, 2),
        (3, 1),
        (3, 1),
        (0, 0),
    ]
    assert [cmd["color"] for cmd in commands] == [[64, 64, 64, 0]] * 2 + [[0] * 4] * 2
    backend.close()
    assert controller["mode"] == "live"


def test_restores_live_mode_if_test_response_is_lost(controller):
    backend = Backend("pixlite.local")
    controller["timeout"] = True
    with pytest.raises(RuntimeError, match="response lost"):
        backend.set_led(0, True)
    backend.close()
    assert controller["mode"] == "live"


def test_refuses_to_interrupt_playback(controller):
    backend = Backend("pixlite.local")
    controller["mode"] = "playback"
    with pytest.raises(RuntimeError, match="live mode"):
        backend.blackout()
    backend.close()
    assert controller["mode"] == "playback"
    assert controller["commands"] == []


def test_does_not_restore_mode_after_initial_rejection(controller):
    backend = Backend("pixlite.local")
    controller["reject"] = True
    with pytest.raises(PixLiteRequestError, match="unauthorized"):
        backend.set_led(0, True)
    controller["mode"] = "playback"
    backend.close()
    assert controller["mode"] == "playback"


@pytest.mark.parametrize(
    ("count", "null_pixels", "group", "expected", "scan_points"),
    [
        (8, 2, 4, 2, [1, 2]),
        (10, 2, 4, 2, [1, 2]),
        (8, 2, 1, 6, [1, 2, 3, 4, 5, 6]),
        (8, 0, 4, 2, [1, 2]),
        (8, 8, 1, 0, []),
    ],
)
def test_logical_pixel_count_and_port_boundary(
    controller, count, null_pixels, group, expected, scan_points
):
    controller["counts"] = [count, 0, 2, 0]
    controller["null_pixels"] = [null_pixels, 0, 0, 0]
    controller["groups"] = [group, 0, 1, 0]
    backend = Backend("pixlite.local")

    assert backend.get_led_count() == expected + 2
    for index in range(expected):
        backend.set_led(index, True)
    assert [command["pixPortNum"] for command in controller["commands"]] == [
        1
    ] * expected
    assert [command["pixNum"] for command in controller["commands"]] == scan_points
    if expected:
        backend.set_led(expected - 1, False)
        assert controller["commands"][-1]["pixNum"] == scan_points[-1]
        assert controller["commands"][-1]["color"] == [0] * 4
    backend.set_led(expected, True)
    assert controller["commands"][-1]["pixPortNum"] == 3
    assert controller["commands"][-1]["pixNum"] == 1
    backend.close()


@pytest.mark.parametrize("physical_ports", [4, 16], ids=["A4", "E16"])
@pytest.mark.parametrize("expanded", [False, True], ids=["normal", "expanded"])
@pytest.mark.parametrize("color_type", ["RGB", "RGBW", "RGBWX"])
@pytest.mark.parametrize("in_format", ["8Bit", "16BitHL", "16BitLH"])
def test_every_port_and_pixel_footprint(
    controller, physical_ports, expanded, color_type, in_format
):
    port_count = physical_ports * (2 if expanded else 1)
    # Exercise unused, all-null and partial-group ports on both device layouts.
    layouts = [(3, 0, 1, 3), (0, 0, 1, 0), (4, 4, 1, 0), (8, 2, 4, 2)]
    active_layouts = [layouts[index % 4] for index in range(port_count)]
    controller.update(
        pix_ports=physical_ports,
        expanded=expanded,
        color_type=color_type,
        in_format=in_format,
        counts=[row[0] for row in active_layouts],
        null_pixels=[row[1] for row in active_layouts],
        groups=[row[2] for row in active_layouts],
    )
    if not expanded:
        # Some firmware includes inactive expanded entries in config responses.
        controller["counts"] += [99] * physical_ports
        controller["null_pixels"] += [0] * physical_ports
        controller["groups"] += [1] * physical_ports

    backend = Backend("pixlite.local")
    channels = {"RGB": 3, "RGBW": 4, "RGBWX": 5}[color_type]
    assert backend.channel_footprint == channels * (1 if in_format == "8Bit" else 2)
    assert backend.get_led_count() == 5 * (port_count // 4)
    led_index = 0
    for port, (_, _, _, count) in enumerate(active_layouts, start=1):
        for local_index in range(count):
            backend.set_led(led_index, True)
            command = controller["commands"][-1]
            assert (command["pixPortNum"], command["pixNum"]) == (port, local_index + 1)
            assert command["colorRes"] == "8Bit"
            assert command["color"] == [64] * 3 + [0] * (channels - 3)
            backend.set_led(led_index, False)
            assert controller["commands"][-1]["color"] == [0] * channels
            led_index += 1
    with pytest.raises(IndexError):
        backend.set_led(led_index, True)
    backend.close()
    assert controller["mode"] == "live"


@pytest.mark.parametrize(
    "settings",
    [
        {"expanded": True, "can_expand": False},
        {"color_type": "RGBW", "color_types": ["RGB"]},
        {"in_format": "16BitHL", "bit_res": 8},
    ],
)
def test_rejects_settings_incompatible_with_pixel_constants(controller, settings):
    controller.update(settings)
    with pytest.raises(RuntimeError, match="PixLite pixel type"):
        Backend("pixlite.local")
    assert controller["commands"] == []


def test_rejects_invalid_settings_on_last_expanded_port(controller):
    controller.update(
        pix_ports=16, counts=[8] * 32, null_pixels=[0] * 32, groups=[1] * 31 + [0]
    )
    with pytest.raises(RuntimeError, match="port 32 has invalid pixel settings"):
        Backend("pixlite.local")
    assert controller["commands"] == []


def test_rejects_missing_expanded_port_entries(controller):
    controller.update(pix_ports=4, counts=[8] * 4)
    with pytest.raises(RuntimeError, match="incomplete pixel port configuration"):
        Backend("pixlite.local")


def test_http_success_can_contain_a_controller_rejection(monkeypatch):
    backend = Backend.__new__(Backend)
    backend.api_url = "https://pixlite.local:4443/v1.9/?user=admin"
    response = Mock(spec=requests.Response, status_code=200)
    response.json.return_value = {"resp": "modeTestData", "id": 1, "err": {"code": 10}}
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: response)

    with pytest.raises(PixLiteRequestError, match="modeTestData.*code 10"):
        backend._request("modeTestData")


def test_detector_reports_child_exit_before_backend_count():
    from marimapper.detector_process import DetectorProcess

    detector = DetectorProcess(
        device=0,
        dark_exposure=-10,
        threshold=128,
        backend_factory=partial(os._exit, 1),
    )
    detector.start()
    try:
        with pytest.raises(RuntimeError, match="before reporting its count"):
            detector.get_led_count()
    finally:
        detector.join(timeout=5)
