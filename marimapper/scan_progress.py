import re
import shutil
import sys
import time

try:  # colorama comes with tqdm on Windows and makes the colour codes work in older consoles
    import colorama

    colorama.just_fix_windows_console()
except Exception:  # not installed, or an older version, plain text is fine
    colorama = None

YELLOW = "\033[33m"
RED = "\033[31m"
RESET = "\033[0m"


def colour(text: str, code: str, enabled=None) -> str:
    """Colours text when the output is a terminal (stderr unless told otherwise)"""
    if sys.stderr.isatty() if enabled is None else enabled:
        return f"{code}{text}{RESET}"
    return text


class CameraStats:
    """
    What one camera has seen so far during a scan. The leds are scanned in order, so a gap is a
    run of missed leds that ends when the camera detects an led again. Leds before the first
    detection or after the last one aren't gaps, they're just outside what the camera can see.
    """

    def __init__(self):
        self.tried = 0
        self.detected = 0
        self.last_detected = None
        self.gaps: list[tuple[int, int]] = []  # (first missed led, last missed led)

    def add(self, led_id: int, found: bool) -> None:
        self.tried += 1

        if not found:
            return

        if self.last_detected is not None and led_id - self.last_detected > 1:
            self.gaps.append((self.last_detected + 1, led_id - 1))

        self.detected += 1
        self.last_detected = led_id

    def percentage(self) -> float:
        return 100.0 * self.detected / self.tried if self.tried else 0.0

    def fillable_gaps(self, max_fill: int) -> list[tuple[int, int]]:
        return [gap for gap in self.gaps if gap_length(gap) <= max_fill]

    def long_gaps(self, max_fill: int) -> list[tuple[int, int]]:
        return [gap for gap in self.gaps if gap_length(gap) > max_fill]

    def summary(self, max_fill: int, use_colour=None) -> str:
        """The gaps for the end of the camera's progress line, picked out in colour, or nothing if there are none"""
        if not self.gaps:
            return ""

        fillable = self.fillable_gaps(max_fill)
        long = self.long_gaps(max_fill)
        parts = []

        if fillable:
            parts.append(colour(f"{len(fillable)} fillable", YELLOW, use_colour))
        if long:
            longest = max(long, key=gap_length)
            parts.append(
                colour(
                    f"{len(long)} too long (longest: LEDs {longest[0]}-{longest[1]})",
                    RED,
                    use_colour,
                )
            )

        return "gaps: " + ", ".join(parts)

    def report(self, max_fill: int) -> list[str]:
        """The gaps the reconstruction can't fill in by itself, one line each"""
        return [
            f"LEDs {start}-{end} ({gap_length((start, end))} in a row) weren't detected"
            for start, end in self.long_gaps(max_fill)
        ]


def gap_length(gap: tuple[int, int]) -> int:
    return gap[1] - gap[0] + 1


def bar(fraction: float, width: int = 20, unicode: bool = True) -> str:
    filled = int(round(max(0.0, min(1.0, fraction)) * width))
    full, empty = ("█", "░") if unicode else ("#", " ")
    return full * filled + empty * (width - filled)


def visible_length(text: str) -> int:
    """The number of characters you see, without the colour codes"""
    length, skipping = 0, False
    for char in text:
        if char == "\033":
            skipping = True
        elif skipping:
            skipping = char != "m"
        else:
            length += 1
    return length


def clock(seconds: float) -> str:
    seconds = int(max(0, seconds))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


class ScanDisplay:
    """
    The progress of a scan: a line for the whole scan and a line for every camera with how many leds that
    camera has detected and where it has gaps. On a terminal the lines are redrawn in place, otherwise
    (a log file, a pipe) only the final state is written.
    """

    def __init__(self, led_count: int, camera_count: int, stream=None, width=None):
        self.led_count = led_count
        self.camera_count = camera_count
        self.stream = stream if stream is not None else sys.stderr
        self.interactive = self.stream.isatty()
        self.width = width  # None: ask the terminal every time, it can be resized
        self.lines_drawn = 0
        self.start = time.time()
        self.unicode = self._can_encode()
        self._last = None  # what was drawn last, to redraw it after a message

    def _can_encode(self) -> bool:
        try:
            "█░".encode(self.stream.encoding or "ascii")
            return True
        except (UnicodeEncodeError, LookupError):
            return False

    def _terminal_width(self) -> int:
        return self.width or shutil.get_terminal_size((100, 24)).columns

    def lines(self, leds_done: int, stats: list, max_fill: int) -> list[str]:
        elapsed = time.time() - self.start
        remaining = (
            elapsed * (self.led_count - leds_done) / leds_done if leds_done else 0
        )
        fraction = leds_done / self.led_count if self.led_count else 1.0

        lines = [
            self._fit(
                f"{'Overall':<9}{100 * fraction:4.0f}%|{bar(fraction, 20, self.unicode)}| "
                f"{leds_done}/{self.led_count} LEDs [{clock(elapsed)}<{clock(remaining)}]"
            )
        ]

        for camera, camera_stats in enumerate(stats):
            line = (
                f"{f'Camera {camera + 1}':<9}detected {camera_stats.percentage():3.0f}%"
                f"|{bar(camera_stats.percentage() / 100, 20, self.unicode)}| "
                f"{camera_stats.detected}/{camera_stats.tried} found"
            )
            gaps = camera_stats.summary(max_fill, self.interactive)
            if gaps:
                line += ", " + gaps
            lines.append(self._fit(line))

        return lines

    def _fit(self, line: str) -> str:
        """A line that is longer than the terminal would wrap and spoil the redrawing"""
        room = self._terminal_width() - 1
        if visible_length(line) <= room:
            return line
        plain = re.sub(r"\033\[[0-9;]*m", "", line)
        return plain[: max(room - 1, 0)] + "…"

    def _erase(self) -> None:
        if self.interactive and self.lines_drawn:
            self.stream.write(f"\033[{self.lines_drawn}A")
            self.stream.write("\033[J")  # clear from here to the end of the screen
            self.lines_drawn = 0

    def draw(self, leds_done: int, stats: list, max_fill: int) -> None:
        if not self.interactive:
            return
        self._erase()
        lines = self.lines(leds_done, stats, max_fill)
        self.stream.write("\n".join(lines) + "\n")
        self.stream.flush()
        self.lines_drawn = len(lines)
        self._last = (leds_done, stats, max_fill)

    def write(self, message: str) -> None:
        """Prints a message above the lines without spoiling them"""
        self._erase()
        self.stream.write(message + "\n")
        self.stream.flush()
        if self._last is not None:
            self.draw(*self._last)

    def finish(self, leds_done: int, stats: list, max_fill: int) -> None:
        """Leaves the final state on screen, and says which gaps can't be filled in"""
        if self.interactive:
            self.draw(leds_done, stats, max_fill)
        else:
            self.stream.write("\n".join(self.lines(leds_done, stats, max_fill)) + "\n")
            self.stream.flush()
