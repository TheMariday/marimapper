from marimapper.queues import DetectionControlEnum
from marimapper.scanner import Scanner


class FakeUpdateQueue:
    """Hands out a prepared list of events, like the queue the detector fills"""

    def __init__(self, events):
        self.events = list(events)

    def get(self):
        return self.events.pop(0)


def make_scanner(view_count, events):
    # no processes or cameras are needed to follow a scan
    scanner = Scanner.__new__(Scanner)
    vars(scanner).update(
        view_count=view_count,
        current_view=0,
        led_id_range=range(0, 5),
        interpolation_max_fill=5,
        detector_update_queue=FakeUpdateQueue(events),
    )
    return scanner


def test_a_scan_waits_for_the_view_of_every_camera():
    events = [(DetectionControlEnum.DONE, 4), (DetectionControlEnum.DONE, 5)]
    scanner = make_scanner(2, events)

    assert scanner.wait_for_scan() is True
    assert (
        scanner.detector_update_queue.events == []
    )  # it didn't stop after the first camera


def test_one_good_view_is_a_successful_scan_even_if_another_was_deleted():
    events = [(DetectionControlEnum.DELETE, 4), (DetectionControlEnum.DONE, 5)]

    assert make_scanner(2, events).wait_for_scan() is True


def test_a_scan_where_every_view_is_deleted_is_not_a_success():
    events = [(DetectionControlEnum.DELETE, 4), (DetectionControlEnum.DELETE, 5)]

    assert make_scanner(2, events).wait_for_scan() is False


def test_a_failed_scan_stops_straight_away():
    events = [(DetectionControlEnum.FAIL, None)]

    assert make_scanner(2, events).wait_for_scan() is False
