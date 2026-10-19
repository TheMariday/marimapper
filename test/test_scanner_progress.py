import io
import re

from marimapper.led import LED2D, Point2D
from marimapper.queues import DetectionControlEnum
from marimapper.scan_progress import CameraStats, ScanDisplay, visible_length
from marimapper.scanner import NO_DETECTION_WARNING_AFTER, Scanner


class FakeUpdateQueue:
    """Hands out a prepared list of events, like the queue the detector fills"""

    def __init__(self, events):
        self.events = list(events)

    def get(self):
        return self.events.pop(0)


class FakeTerminal(io.StringIO):
    isatty_result = True
    encoding = "utf-8"

    def isatty(self):
        return self.isatty_result


def make_scanner(view_count, current_view, led_count, events, max_fill=5):
    scanner = Scanner.__new__(
        Scanner
    )  # no processes or cameras needed to follow a scan
    scanner.view_count = view_count
    scanner.current_view = current_view
    scanner.led_id_range = range(0, led_count)
    scanner.interpolation_max_fill = max_fill
    scanner.detector_update_queue = FakeUpdateQueue(events)
    return scanner


def detect(led_id, view_id):
    return DetectionControlEnum.DETECT, LED2D(led_id, view_id, Point2D(0.5, 0.5))


def skip(led_id):
    return DetectionControlEnum.SKIP, led_id


def final_lines(capsys):
    """The lines a log would end up with (output isn't a terminal in tests), and the other output"""
    captured = capsys.readouterr()
    lines = {}
    for line in captured.err.splitlines():
        for name in ("Overall", "Camera 1", "Camera 2"):
            if line.startswith(name):
                lines[name] = line
    return lines, captured.err, captured.out


def test_camera_stats_find_the_gaps_between_detections():
    stats = CameraStats()
    for led_id in range(12):
        stats.add(
            led_id, led_id in (2, 3, 4, 8, 9)
        )  # nothing before 2, a gap at 5-7, nothing after 9

    assert stats.tried == 12
    assert stats.detected == 5
    assert stats.gaps == [(5, 7)]  # the leds outside what the camera sees aren't gaps
    assert stats.percentage() == 100.0 * 5 / 12


def test_camera_stats_tell_gaps_that_can_be_filled_from_those_that_cant():
    stats = CameraStats()
    for led_id in range(30):
        stats.add(led_id, led_id not in (4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21))

    assert stats.gaps == [(4, 5), (12, 21)]
    assert stats.fillable_gaps(max_fill=5) == [(4, 5)]
    assert stats.long_gaps(max_fill=5) == [(12, 21)]
    assert (
        stats.summary(max_fill=5, use_colour=False)
        == "gaps: 1 fillable, 1 too long (longest: LEDs 12-21)"
    )
    assert stats.report(max_fill=5) == ["LEDs 12-21 (10 in a row) weren't detected"]


def test_camera_stats_without_gaps_say_nothing_about_gaps():
    stats = CameraStats()
    for led_id in range(5):
        stats.add(led_id, True)

    assert stats.summary(max_fill=5) == ""
    assert stats.report(max_fill=5) == []


def test_gaps_are_coloured_on_a_terminal_only():
    stats = CameraStats()
    for led_id in range(20):
        stats.add(led_id, led_id not in (4, 12, 13, 14, 15, 16, 17, 18))

    assert "\033[" in stats.summary(max_fill=5, use_colour=True)
    assert "\033[" not in stats.summary(max_fill=5, use_colour=False)


def test_there_is_an_overall_line_and_one_line_per_camera(capsys):
    leds = NO_DETECTION_WARNING_AFTER + 5
    events = []
    for led_id in range(leds):
        events.append(detect(led_id, 4))  # camera 1 sees every led
        events.append(skip(led_id))  # camera 2 sees none
    events += [
        (DetectionControlEnum.DONE, 4),
        (DetectionControlEnum.DELETE, 5),  # camera 2's view had nothing in it
    ]

    assert (
        make_scanner(2, 4, leds, events).wait_for_scan() is True
    )  # one good view is enough

    lines, err, _ = final_lines(capsys)
    assert re.search(rf"Overall\s+100%.*{leds}/{leds} LEDs", lines["Overall"])
    assert re.search(
        rf"Camera 1\s+detected\s+100%.*{leds}/{leds} found", lines["Camera 1"]
    )
    assert re.search(rf"Camera 2\s+detected\s+0%.*0/{leds} found", lines["Camera 2"])

    # the camera that saw nothing is named, once, not for every led
    assert "Camera 2 hasn't detected any of the first" in err
    assert "Camera 1 hasn't detected" not in err
    assert err.count("hasn't detected any") == 1


def test_every_camera_shows_its_own_detection_rate_and_gaps(capsys):
    # camera 1 sees the even leds, camera 2 the odd ones
    events = []
    for led_id in range(10):
        events.append(detect(led_id, 0) if led_id % 2 == 0 else skip(led_id))
        events.append(detect(led_id, 1) if led_id % 2 == 1 else skip(led_id))
    events += [(DetectionControlEnum.DONE, 0), (DetectionControlEnum.DONE, 1)]

    assert make_scanner(2, 0, 10, events).wait_for_scan() is True

    lines, _, _ = final_lines(capsys)
    assert re.search(
        r"Camera 1\s+detected\s+50%.*5/10 found, gaps: 4 fillable", lines["Camera 1"]
    )
    assert re.search(
        r"Camera 2\s+detected\s+50%.*5/10 found, gaps: 4 fillable", lines["Camera 2"]
    )


def test_gaps_that_are_too_long_are_pointed_out_when_the_scan_ends(capsys):
    # camera 1 loses leds 3 to 12, which is more than the 5 that can be filled in
    events = []
    for led_id in range(20):
        events.append(skip(led_id) if 3 <= led_id <= 12 else detect(led_id, 0))
    events.append((DetectionControlEnum.DONE, 0))

    assert make_scanner(1, 0, 20, events, max_fill=5).wait_for_scan() is True

    lines, _, out = final_lines(capsys)
    assert "1 too long (longest: LEDs 3-12)" in lines["Camera 1"]
    assert "LEDs 3-12 (10 in a row) weren't detected" in out


def test_a_scan_where_every_view_is_deleted_is_not_a_success():
    events = [
        (DetectionControlEnum.DELETE, 0),
        (DetectionControlEnum.DELETE, 1),
    ]

    assert make_scanner(2, 0, 5, events).wait_for_scan() is False


def test_a_failed_scan_stops_straight_away():
    events = [(DetectionControlEnum.FAIL, None)]

    assert make_scanner(2, 0, 5, events).wait_for_scan() is False


def three_cameras():
    stats = [CameraStats() for _ in range(3)]
    for camera, camera_stats in enumerate(stats):
        for led_id in range(10):
            camera_stats.add(led_id, (led_id + camera) % 3 != 0)
    return stats


def test_on_a_terminal_the_lines_are_redrawn_in_place():
    terminal = FakeTerminal()
    display = ScanDisplay(led_count=10, camera_count=3, stream=terminal, width=200)
    stats = three_cameras()

    display.draw(5, stats, max_fill=5)
    first = terminal.getvalue()
    assert (
        first.count("\n") == 4
    )  # the overall line and a line for each of the 3 cameras

    display.draw(6, stats, max_fill=5)
    second = terminal.getvalue()[len(first) :]
    assert second.startswith(
        "\033[4A\033[J"
    )  # back up over the 4 lines, clear, draw again
    assert second.count("\n") == 4

    lines = second[len("\033[4A\033[J") :].splitlines()
    assert [line.split()[0] for line in lines] == [
        "Overall",
        "Camera",
        "Camera",
        "Camera",
    ]
    assert [line.split()[1] for line in lines[1:]] == ["1", "2", "3"]  # in camera order


def test_a_message_goes_above_the_lines_and_they_are_drawn_again():
    terminal = FakeTerminal()
    display = ScanDisplay(led_count=10, camera_count=3, stream=terminal, width=200)
    display.draw(5, three_cameras(), max_fill=5)
    before = len(terminal.getvalue())

    display.write("Camera 2 needs a look")

    after = terminal.getvalue()[before:]
    assert after.startswith("\033[4A\033[J" + "Camera 2 needs a look\n")
    assert after.count("\n") == 1 + 4  # the message, then the 4 lines again


def test_lines_are_trimmed_to_the_width_of_the_terminal():
    terminal = FakeTerminal()
    display = ScanDisplay(led_count=10, camera_count=3, stream=terminal, width=60)

    lines = display.lines(5, three_cameras(), max_fill=5)

    assert all(
        visible_length(line) <= 59 for line in lines
    )  # a line that wraps spoils the redrawing


def test_without_a_terminal_only_the_final_state_is_written():
    log = FakeTerminal()
    log.isatty_result = False
    display = ScanDisplay(led_count=10, camera_count=3, stream=log, width=200)
    stats = three_cameras()

    display.draw(3, stats, max_fill=5)
    display.draw(7, stats, max_fill=5)
    assert log.getvalue() == ""  # no half-finished lines in a log

    display.finish(10, stats, max_fill=5)
    assert log.getvalue().count("\n") == 4
    assert "\033" not in log.getvalue()  # no colour or cursor codes either


def test_a_terminal_that_cant_show_block_characters_gets_plain_ones():
    terminal = FakeTerminal()
    terminal.encoding = "ascii"
    display = ScanDisplay(led_count=10, camera_count=1, stream=terminal, width=200)

    line = display.lines(5, [CameraStats()], max_fill=5)[0]

    assert "█" not in line and "#" in line
