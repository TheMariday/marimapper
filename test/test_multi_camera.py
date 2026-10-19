import time

import cv2
import numpy
import pytest
from marimapper.camera import open_cameras
from marimapper.detector import enable_and_find_led, enable_and_find_leds, find_leds
from marimapper.detector_process import detect_leds
from marimapper.file_writer_process import FileWriterProcess
from marimapper.queues import DetectionControlEnum
from marimapper.timeout_controller import TimeoutController


class FakeScene:
    """
    A tiny world to test detection without cameras: positions[camera][led_id] is where
    that camera sees that led (pixels), or missing if it can't see it.
    """

    def __init__(self, positions, always_bright=()):
        self.positions = positions
        self.always_bright = (
            always_bright  # cameras that always see some light, like a reflection
        )
        self.lit = None


class FakeBackend:
    def __init__(self, scene):
        self.scene = scene

    def set_led(self, led_id, state):
        if state:
            self.scene.lit = led_id
        elif self.scene.lit == led_id:
            self.scene.lit = None


class FakeCamera:
    def __init__(self, scene, index):
        self.scene = scene
        self.index = index

    def grab(self):
        pass

    def retrieve(self):
        image = numpy.zeros((480, 640, 3), dtype=numpy.uint8)

        if self.index in self.scene.always_bright:
            image[10:18, 10:18] = 255

        position = self.scene.positions[self.index].get(self.scene.lit)
        if position is not None:
            x, y = position
            image[y : y + 8, x : x + 8] = 255

        return image

    def read(self):
        return self.retrieve()


class FakeQueue:
    def __init__(self):
        self.items = []

    def put(self, control, data):
        self.items.append((control, data))


def make_world(positions, always_bright=()):
    scene = FakeScene(positions, always_bright)
    cams = [FakeCamera(scene, index) for index in range(len(positions))]
    return scene, cams, FakeBackend(scene)


def fast_timeout():
    return TimeoutController(default_timeout_sec=0.2, sample_size_min=3)


def test_find_leds_looks_in_every_camera():
    _, cams, _ = make_world([{}, {}])
    cams[1].scene.lit = 0
    cams[1].scene.positions[1][0] = (300, 200)

    results = find_leds(cams, display=False)

    assert results[0] is None
    assert results[1] is not None


def test_led_seen_by_all_cameras_gives_one_result_per_camera():
    _, cams, backend = make_world([{3: (100, 100)}, {3: (400, 300)}])

    leds = enable_and_find_leds(
        cams, backend, 3, [10, 11], fast_timeout(), threshold=128
    )

    assert [led.view_id for led in leds] == [10, 11]
    assert [led.led_id for led in leds] == [3, 3]
    # the two cameras see it in different places
    assert leds[0].point.u() == pytest.approx(104 / 640, abs=0.02)
    assert leds[1].point.u() == pytest.approx(404 / 640, abs=0.02)


def test_led_seen_by_only_one_camera():
    _, cams, backend = make_world([{3: (100, 100)}, {}])

    leds = enable_and_find_leds(
        cams, backend, 3, [10, 11], fast_timeout(), threshold=128
    )

    assert leds[0] is not None and leds[0].view_id == 10
    assert leds[1] is None


def test_led_seen_by_nobody_leaves_the_timeout_alone():
    _, cams, backend = make_world([{}, {}])
    timeout_controller = fast_timeout()

    leds = enable_and_find_leds(cams, backend, 3, [10, 11], timeout_controller, 128)

    assert leds == [None, None]
    assert timeout_controller._response_times == []


def test_a_camera_that_never_sees_the_led_does_not_inflate_the_timeout():
    # camera 1 never sees anything, so every led waits out the timeout for it. If that wait counted
    # as a response time, the timeout would grow by 50% each time.
    positions = [{led: (100, 100) for led in range(8)}, {}]
    _, cams, backend = make_world(positions)
    timeout_controller = TimeoutController(default_timeout_sec=0.1, sample_size_min=3)

    for led_id in range(8):
        enable_and_find_leds(cams, backend, led_id, [0, 1], timeout_controller, 128)

    assert timeout_controller.timeout < 0.1


def test_a_camera_that_always_sees_light_is_ignored_but_the_others_still_work():
    positions = [{3: (100, 100)}, {3: (400, 300)}]
    _, cams, backend = make_world(positions, always_bright=[1])

    start = time.time()
    leds = enable_and_find_leds(
        cams, backend, 3, [10, 11], fast_timeout(), threshold=128
    )

    assert time.time() - start > 3.0  # it gave the camera its three seconds to go dark
    assert leds[0] is not None
    assert leds[1] is None


def test_single_camera_is_unchanged():
    _, cams, backend = make_world([{5: (200, 150)}])

    led = enable_and_find_led(cams[0], backend, 5, 7, fast_timeout(), 128)

    assert led.led_id == 5
    assert led.view_id == 7

    assert (
        enable_and_find_led(cams[0], backend, 6, 7, fast_timeout(), 128) is None
    )  # nobody sees led 6


def test_detect_leds_reports_every_camera_separately():
    positions = [
        {0: (100, 100), 1: (120, 100)},  # camera 0 sees both leds
        {1: (300, 200)},  # camera 1 only sees led 1
    ]
    _, cams, backend = make_world(positions)
    queue = FakeQueue()

    leds_per_camera = detect_leds(
        0, 2, cams, backend, [4, 5], fast_timeout(), 128, False, [queue]
    )

    assert [len(leds) for leds in leds_per_camera] == [2, 1]
    assert {led.view_id for led in leds_per_camera[0]} == {4}
    assert {led.view_id for led in leds_per_camera[1]} == {5}

    detections = [d for c, d in queue.items if c == DetectionControlEnum.DETECT]
    skips = [d for c, d in queue.items if c == DetectionControlEnum.SKIP]
    assert len(detections) == 3
    assert skips == [0]  # camera 1 skipped led 0
    # one event per led per camera, which is what the progress bar counts
    assert len(queue.items) == 2 * 2


def test_cameras_finishing_together_get_different_files(tmp_path):
    writer = FileWriterProcess(tmp_path)

    first = writer.get_new_filename([])
    second = writer.get_new_filename([first])
    third = writer.get_new_filename([first, second])

    assert len({first, second, third}) == 3
    assert all(
        f.parent == tmp_path and f.suffix == ".csv" for f in (first, second, third)
    )


def test_a_file_that_already_exists_is_not_reused(tmp_path):
    writer = FileWriterProcess(tmp_path)

    first = writer.get_new_filename([])
    first.write_text("index,u,v")

    assert writer.get_new_filename([]) != first


def fake_video_capture(monkeypatch, can_open, can_read=None):
    """
    Replaces OpenCV's cameras: can_open says which cameras each capture method can open
    (a camera number for webcams) and can_read which of those really deliver pictures.
    """

    class FakeCapture:
        def __init__(self, device, method, params=None):
            self.device = device
            self.method = method
            self.opened = device in can_open.get(method, ())

        def isOpened(self):
            return self.opened

        def read(self):
            readable = (can_read or can_open).get(self.method, ())
            if self.device in readable:
                return True, numpy.zeros((4, 4, 3), dtype=numpy.uint8)
            return False, None

        def get(self, prop):
            return 0

        def set(self, prop, value):
            return True

        def release(self):
            self.opened = False

    monkeypatch.setattr(cv2, "VideoCapture", FakeCapture)


def test_cameras_are_all_opened_with_the_same_capture_method(monkeypatch):
    # DirectShow can open camera 2 but not camera 1: using it for camera 2 and the default method
    # for camera 1 would number the cameras two different ways
    fake_video_capture(monkeypatch, {cv2.CAP_DSHOW: {2}, cv2.CAP_ANY: {1, 2}})

    cams = open_cameras([1, 2])

    assert [cam.device.method for cam in cams] == [cv2.CAP_ANY, cv2.CAP_ANY]
    assert [cam.device.device for cam in cams] == [1, 2]


def test_cameras_that_open_but_deliver_nothing_are_rejected(monkeypatch):
    fake_video_capture(
        monkeypatch,
        {cv2.CAP_DSHOW: {1, 2}, cv2.CAP_ANY: {1, 2}},
        can_read={
            cv2.CAP_DSHOW: {1},
            cv2.CAP_ANY: {1},
        },  # camera 2 never gives a picture
    )

    with pytest.raises(RuntimeError, match="USB"):
        open_cameras([1, 2])


def test_a_single_camera_still_tries_every_method_on_its_own(monkeypatch):
    fake_video_capture(monkeypatch, {cv2.CAP_ANY: {2}})

    cams = open_cameras(2)

    assert len(cams) == 1
    assert cams[0].device.method == cv2.CAP_ANY


def test_network_cameras_are_opened_on_their_own_and_keep_their_place(monkeypatch):
    url = "http://192.168.1.20:4747/video"
    fake_video_capture(
        monkeypatch,
        {cv2.CAP_DSHOW: {1, 2}, cv2.CAP_FFMPEG: {url}, cv2.CAP_ANY: {url}},
    )

    cams = open_cameras([1, url, 2])

    assert [cam.device.device for cam in cams] == [1, url, 2]
    assert cams[0].device.method == cams[2].device.method == cv2.CAP_DSHOW
