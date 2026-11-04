import pytest

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
            return {"constant": {"dev": {"pixPorts": 2}}}
        if name == "configRead":
            return {
                "config": {
                    "pix": {"expand": True, "colorType": "RGBW"},
                    "pixPort": {
                        "pixCount": state["counts"],
                        "nullPix": state.get("null_pixels", [0, 0, 0, 0]),
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


def test_rejects_null_pixels_on_active_ports(controller):
    controller["null_pixels"] = [0, 0, 1, 0]
    with pytest.raises(RuntimeError, match="null pixels"):
        Backend("pixlite.local")
