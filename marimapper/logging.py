# You might be wondering why this file exists.
# Well, this is because the default logging library does //not// like multiprocessing, so to save
# my sanity, I've implemented the worlds most basic logging library so that I can at least see something
# No this isn't multiprocessing "safe" but again, it's something


class Col:
    PURPLE = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def colorise(string, string_format):
    return f"{string_format}{string}\033[0m"


def debug(string):
    print(colorise(string, Col.BOLD))


def error(string):
    print(colorise(string, Col.FAIL))


def warn(string):
    print(colorise(string, Col.WARNING))


def info(string):
    print(string)
