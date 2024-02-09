class Col:
    PURPLE = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def cprint(str, format=""):
    print(f"{format}{str}\033[0m")


if __name__ == "__main__":
    cprint("hello")
    cprint("hello", Col.PURPLE)
    cprint("hello", Col.BLUE)
    cprint("hello", Col.CYAN)
    cprint("hello", Col.GREEN)
    cprint("hello", Col.WARNING)
    cprint("hello", Col.FAIL)
    cprint("hello", Col.BOLD)
    cprint("hello", Col.UNDERLINE)
