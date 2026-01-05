from viser import _messages
from viser.theme import TitlebarButton, TitlebarImage, TitlebarConfig

THEME_PRIMARY = "#034AA6"
THEME_SECONDARY = "#049DD9"

class Color:
    READY = (0, 0, 255)
    PROCESSING = (0,255,0)
    WARNING = (255,128,128)
    ERROR = (255,0,0)
    DEFAULT = (0,0,128)
    YES = (0,255,0)
    NO = (255,0,0)
    CONFIRM = YES

def populate_theme(gui):
    buttons = (
        TitlebarButton(
            text="Help",
            icon="Description",
            href="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        ),
        TitlebarButton(
            text="Github",
            icon="GitHub",
            href="https://github.com/nerfstudio-project/nerfstudio",
        ),
    )
    image = TitlebarImage(
        image_url_light="https://gcdnb.pbrd.co/images/egyusIRKgbWg.png?o=1",
        image_url_dark="https://gcdnb.pbrd.co/images/egyusIRKgbWg.png?o=1",
        image_alt="marimapper Logo",
        href="https://github.com/TheMariday/marimapper/",
    )

    cols = list("#ffffff" for _ in range(10))
    cols[6] = THEME_SECONDARY
    cols[7] = THEME_PRIMARY

    gui._websock_interface.queue_message(
        _messages.ThemeConfigurationMessage(
            titlebar_content=TitlebarConfig(buttons=buttons, image=image),
            control_layout="floating",
            control_width="large",
            dark_mode=False,
            show_logo=True,
            show_share_button=True,
            colors=cols
        ),
    )